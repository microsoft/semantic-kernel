// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Events;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a function that can be invoked as part of a Semantic Kernel workload.
/// </summary>
public abstract class KernelFunction
{
    /// <summary><see cref="ActivitySource"/> for function-related activities.</summary>
    private static readonly ActivitySource s_activitySource = new("Microsoft.SemanticKernel");

    /// <summary><see cref="Meter"/> for function-related metrics.</summary>
    private static readonly Meter s_meter = new("Microsoft.SemanticKernel");

    /// <summary><see cref="Histogram{T}"/> to record function invocation duration.</summary>
    private static readonly Histogram<double> s_invocationDuration = s_meter.CreateHistogram<double>(
        name: "sk.function.duration",
        unit: "s",
        description: "Measures the duration of a function’s execution");

    /// <summary>
    /// Gets the name of the function.
    /// </summary>
    /// <remarks>
    /// The name is used anywhere the function needs to be identified, such as in plans describing what functions
    /// should be invoked when, or as part of lookups in a plugin's function collection. Function names are generally
    /// handled in an ordinal case-insensitive manner.
    /// </remarks>
    public string Name => this.Metadata.Name;

    /// <summary>
    /// Gets a description of the function.
    /// </summary>
    /// <remarks>
    /// The description may be supplied to a model in order to elaborate on the function's purpose,
    /// in case it may be beneficial for the model to recommend invoking the function.
    /// </remarks>
    public string Description => this.Metadata.Description;

    /// <summary>
    /// Gets the metadata describing the function.
    /// </summary>
    /// <returns>An instance of <see cref="KernelFunctionMetadata"/> describing the function</returns>
    public KernelFunctionMetadata Metadata { get; init; }

    /// <summary>
    /// Gets the prompt execution settings.
    /// </summary>
    internal IEnumerable<PromptExecutionSettings> ExecutionSettings { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelFunction"/> class.
    /// </summary>
    /// <param name="name">Name of the function.</param>
    /// <param name="description">Function description.</param>
    /// <param name="parameters">Function parameters metadata</param>
    /// <param name="returnParameter">Function return parameter metadata</param>
    /// <param name="executionSettings">Prompt execution settings.</param>
    internal KernelFunction(string name, string description, IReadOnlyList<KernelParameterMetadata> parameters, KernelReturnParameterMetadata? returnParameter = null, IEnumerable<PromptExecutionSettings>? executionSettings = null)
    {
        Verify.NotNull(name);
        Verify.ParametersUniqueness(parameters);

        this.Metadata = new KernelFunctionMetadata(name)
        {
            Description = description,
            Parameters = parameters,
            ReturnParameter = returnParameter ?? new()
        };
        this.ExecutionSettings = executionSettings ?? Enumerable.Empty<PromptExecutionSettings>();
    }

    /// <summary>
    /// Execute a function allowing to pass the main input separately from the rest of the context.
    /// </summary>
    /// <param name="kernel">Kernel</param>
    /// <param name="input">Input string for the function</param>
    /// <param name="executionSettings">LLM completion settings (for semantic functions only)</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function execution</returns>
    public Task<FunctionResult> InvokeAsync(
        Kernel kernel,
        string input,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        KernelArguments? arguments = executionSettings is not null ? new(executionSettings) : null;
        if (!string.IsNullOrEmpty(input))
        {
            (arguments ??= new()).Add(KernelArguments.InputParameterName, input);
        }

        return this.InvokeAsync(kernel, arguments, cancellationToken);
    }

    /// <summary>
    /// Invoke the <see cref="KernelFunction"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="arguments">The function arguments.</param>
    /// <returns>The updated context, potentially a new one if context switching is implemented.</returns>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public async Task<FunctionResult> InvokeAsync(
        Kernel kernel,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default)
    {
        cancellationToken.ThrowIfCancellationRequested();

        using var activity = s_activitySource.StartActivity(this.Name);
        ILogger logger = kernel.LoggerFactory.CreateLogger(this.Name);

        // Ensure arguments are initialized.
        arguments ??= new KernelArguments();

        if (logger.IsEnabled(LogLevel.Trace))
        {
            logger.LogTrace("Function invoking. Arguments: {Arguments}", string.Join(", ", arguments.Select(v => $"{v.Key}:{v.Value}")));
        }

        TagList tags = new() { { "sk.function.name", this.Name } };
        long startingTimestamp = Stopwatch.GetTimestamp();
        try
        {
            // Invoke pre hook, and stop if skipping requested.
            var invokingEventArgs = kernel.OnFunctionInvoking(this, arguments);
            if (invokingEventArgs is not null && invokingEventArgs.Cancel)
            {
                logger.LogTrace("Function canceled prior to invocation.");

                return new FunctionResult(this.Name)
                {
                    IsCancellationRequested = invokingEventArgs.Cancel,
                };
            }

            var result = await this.InvokeCoreAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);

            logger.LogTrace("Function succeeded.");

            // Invoke the post hook.
            (var invokedEventArgs, result) = this.CallFunctionInvoked(kernel, arguments, result);

            if (logger.IsEnabled(LogLevel.Trace))
            {
                logger.LogTrace("Function invocation {Completion}: {Result}",
                    invokedEventArgs?.Cancel ?? false ? "canceled" : "completed",
                    result.Value);
            }

            result.IsCancellationRequested = invokedEventArgs?.Cancel ?? false;

            return result;
        }
        catch (Exception ex)
        {
            tags.Add("error.type", ex.GetType().FullName);
            if (logger.IsEnabled(LogLevel.Error))
            {
                logger.LogError(ex, "Function failed. Error: {Message}", ex.Message);
            }
            throw;
        }
        finally
        {
            TimeSpan duration = new((long)((Stopwatch.GetTimestamp() - startingTimestamp) * (10_000_000.0 / Stopwatch.Frequency)));
            s_invocationDuration.Record(duration.TotalSeconds, in tags);
            if (logger.IsEnabled(LogLevel.Information))
            {
                logger.LogInformation("Function completed. Duration: {Duration}ms", duration.TotalMilliseconds);
            }
        }
    }

    /// <summary>
    /// Invoke the <see cref="KernelFunction"/> in streaming mode.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="arguments">The function arguments</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A asynchronous list of streaming result chunks</returns>
    public IAsyncEnumerable<StreamingContent> InvokeStreamingAsync(
        Kernel kernel,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default)
    {
        return this.InvokeStreamingAsync<StreamingContent>(kernel, arguments, cancellationToken);
    }

    /// <summary>
    /// Invoke the <see cref="KernelFunction"/> in streaming mode.
    /// </summary>
    /// <param name="kernel">The kernel</param>
    /// <param name="input">Input string for the function</param>
    /// <param name="executionSettings">LLM completion settings (for semantic functions only)</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A asynchronous list of streaming result chunks</returns>
    public IAsyncEnumerable<T> InvokeStreamingAsync<T>(
        Kernel kernel,
        string input,
        PromptExecutionSettings? executionSettings = null,
        CancellationToken cancellationToken = default)
    {
        KernelArguments? arguments = executionSettings is not null ? new(executionSettings) : null;
        if (!string.IsNullOrEmpty(input))
        {
            (arguments ??= new()).Add(KernelArguments.InputParameterName, input);
        }

        return this.InvokeStreamingAsync<T>(kernel, arguments, cancellationToken);
    }

    /// <summary>
    /// Invoke the <see cref="KernelFunction"/> in streaming mode.
    /// </summary>
    /// <param name="kernel">The kernel</param>
    /// <param name="arguments">The function arguments</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A asynchronous list of streaming content chunks</returns>
    public async IAsyncEnumerable<T> InvokeStreamingAsync<T>(
        Kernel kernel,
        KernelArguments? arguments = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using var activity = s_activitySource.StartActivity(this.Name);
        ILogger logger = kernel.LoggerFactory.CreateLogger(this.Name);

        logger.LogInformation("Function streaming invoking.");

        arguments ??= new KernelArguments();

        // Invoke pre hook, and stop if skipping requested.
        var invokingEventArgs = kernel.OnFunctionInvoking(this, arguments);
        if (invokingEventArgs is not null && invokingEventArgs.Cancel)
        {
            logger.LogTrace("Function canceled or skipped prior to invocation.");

            yield break;
        }

        await foreach (var genericChunk in this.InvokeCoreStreamingAsync<T>(kernel, arguments, cancellationToken))
        {
            yield return genericChunk;
        }

        // Completion logging is not supported for streaming functions
        // Invoke post hook not support for streaming functions
    }

    /// <summary>
    /// Invoke as streaming the <see cref="KernelFunction"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="arguments">The kernel function arguments.</param>
    /// <returns>The updated context, potentially a new one if context switching is implemented.</returns>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    protected abstract IAsyncEnumerable<T> InvokeCoreStreamingAsync<T>(Kernel kernel,
        KernelArguments arguments,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Invoke the <see cref="KernelFunction"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="arguments">The kernel function arguments.</param>
    /// <returns>The updated context, potentially a new one if context switching is implemented.</returns>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    protected abstract Task<FunctionResult> InvokeCoreAsync(
        Kernel kernel,
        KernelArguments arguments,
        CancellationToken cancellationToken);

    #region private
    private (FunctionInvokedEventArgs?, FunctionResult) CallFunctionInvoked(Kernel kernel, KernelArguments arguments, FunctionResult result)
    {
        var eventArgs = kernel.OnFunctionInvoked(this, arguments, result);
        if (eventArgs is not null)
        {
            // Apply any changes from the event handlers to final result.
            result = new FunctionResult(this.Name, eventArgs.ResultValue, result.Culture);
            if (eventArgs.Metadata is not null)
            {
                // Updates the eventArgs metadata during invoked handler execution
                // will reflect in the result metadata
                result.Metadata = eventArgs.Metadata;
            };
        }

        return (eventArgs, result);
    }
    #endregion
}

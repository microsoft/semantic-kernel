﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a function that can be invoked as part of a Semantic Kernel workload.
/// </summary>
public abstract class KernelFunction
{
    /// <summary>The measurement tag name for the function name.</summary>
    private protected const string MeasurementFunctionTagName = "semantic_kernel.function.name";

    /// <summary>The measurement tag name for the function error type.</summary>
    private protected const string MeasurementErrorTagName = "error.type";

    /// <summary><see cref="ActivitySource"/> for function-related activities.</summary>
    private static readonly ActivitySource s_activitySource = new("Microsoft.SemanticKernel");

    /// <summary><see cref="Meter"/> for function-related metrics.</summary>
    private protected static readonly Meter s_meter = new("Microsoft.SemanticKernel");

    /// <summary><see cref="Histogram{T}"/> to record function invocation duration.</summary>
    private static readonly Histogram<double> s_invocationDuration = s_meter.CreateHistogram<double>(
        name: "semantic_kernel.function.invocation.duration",
        unit: "s",
        description: "Measures the duration of a function's execution");

    /// <summary><see cref="Histogram{T}"/> to record function streaming duration.</summary>
    /// <remarks>
    /// As this metric spans the full async iterator's lifecycle, it is inclusive of any time
    /// spent in the consuming code between MoveNextAsync calls on the enumerator.
    /// </remarks>
    private static readonly Histogram<double> s_streamingDuration = s_meter.CreateHistogram<double>(
        name: "semantic_kernel.function.streaming.duration",
        unit: "s",
        description: "Measures the duration of a function's streaming execution");

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
    /// Gets the name of the plugin this function was added to.
    /// </summary>
    /// <remarks>
    /// The plugin name will be null if the function has not been added to a plugin.
    /// When a function is added to a plugin it will be cloned and the plugin name will be set.
    /// </remarks>
    public string? PluginName => this.Metadata.PluginName;

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
    /// <remarks>
    /// The instances of <see cref="PromptExecutionSettings"/> are frozen and cannot be modified.
    /// </remarks>
    public IReadOnlyDictionary<string, PromptExecutionSettings>? ExecutionSettings { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelFunction"/> class.
    /// </summary>
    /// <param name="name">A name of the function to use as its <see cref="KernelFunction.Name"/>.</param>
    /// <param name="description">The description of the function to use as its <see cref="KernelFunction.Description"/>.</param>
    /// <param name="parameters">The metadata describing the parameters to the function.</param>
    /// <param name="returnParameter">The metadata describing the return parameter of the function.</param>
    /// <param name="executionSettings">
    /// The <see cref="PromptExecutionSettings"/> to use with the function. These will apply unless they've been
    /// overridden by settings passed into the invocation of the function.
    /// </param>
    internal KernelFunction(string name, string description, IReadOnlyList<KernelParameterMetadata> parameters, KernelReturnParameterMetadata? returnParameter = null, Dictionary<string, PromptExecutionSettings>? executionSettings = null)
        : this(name, null, description, parameters, returnParameter, executionSettings)
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelFunction"/> class.
    /// </summary>
    /// <param name="name">A name of the function to use as its <see cref="KernelFunction.Name"/>.</param>
    /// <param name="pluginName">The name of the plugin this function instance has been added to.</param>
    /// <param name="description">The description of the function to use as its <see cref="KernelFunction.Description"/>.</param>
    /// <param name="parameters">The metadata describing the parameters to the function.</param>
    /// <param name="returnParameter">The metadata describing the return parameter of the function.</param>
    /// <param name="executionSettings">
    /// The <see cref="PromptExecutionSettings"/> to use with the function. These will apply unless they've been
    /// overridden by settings passed into the invocation of the function.
    /// </param>
    /// <param name="additionalMetadata">Properties/metadata associated with the function itself rather than its parameters and return type.</param>
    internal KernelFunction(string name, string? pluginName, string description, IReadOnlyList<KernelParameterMetadata> parameters, KernelReturnParameterMetadata? returnParameter = null, Dictionary<string, PromptExecutionSettings>? executionSettings = null, ReadOnlyDictionary<string, object?>? additionalMetadata = null)
    {
        Verify.NotNull(name);
        Verify.ParametersUniqueness(parameters);

        this.Metadata = new KernelFunctionMetadata(name)
        {
            PluginName = pluginName,
            Description = description,
            Parameters = parameters,
            ReturnParameter = returnParameter ?? KernelReturnParameterMetadata.Empty,
            AdditionalProperties = additionalMetadata ?? KernelFunctionMetadata.s_emptyDictionary,
        };

        if (executionSettings is not null)
        {
            this.ExecutionSettings = executionSettings.ToDictionary(
                entry => entry.Key,
                entry => { var clone = entry.Value.Clone(); clone.Freeze(); return clone; });
        }
    }

    /// <summary>
    /// Invokes the <see cref="KernelFunction"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function's execution.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    public async Task<FunctionResult> InvokeAsync(
        Kernel kernel,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);

        using var activity = s_activitySource.StartActivity(this.Name);
        ILogger logger = kernel.LoggerFactory.CreateLogger(typeof(KernelFunction)) ?? NullLogger.Instance;

        // Ensure arguments are initialized.
        arguments ??= [];
        logger.LogFunctionInvoking(this.Name);
        logger.LogFunctionArguments(arguments);

        TagList tags = new() { { MeasurementFunctionTagName, this.Name } };
        long startingTimestamp = Stopwatch.GetTimestamp();
        FunctionResult functionResult = new(this, culture: kernel.Culture);
        try
        {
            // Quick check for cancellation after logging about function start but before doing any real work.
            cancellationToken.ThrowIfCancellationRequested();

            // Invoke pre-invocation event handler. If it requests cancellation, throw.
#pragma warning disable CS0618 // Events are deprecated
            var invokingEventArgs = kernel.OnFunctionInvoking(this, arguments);
#pragma warning restore CS0618 // Events are deprecated

            if (invokingEventArgs?.Cancel is true)
            {
                throw new OperationCanceledException($"A {nameof(Kernel)}.{nameof(Kernel.FunctionInvoking)} event handler requested cancellation before function invocation.");
            }

            var invocationContext = await kernel.OnFunctionInvocationAsync(this, arguments, functionResult, async (context) =>
            {
                // Invoking the function and updating context with result.
                context.Result = functionResult = await this.InvokeCoreAsync(kernel, context.Arguments, cancellationToken).ConfigureAwait(false);
            }, cancellationToken).ConfigureAwait(false);

            // Apply any changes from the function filters context to final result.
            functionResult = invocationContext.Result;

            // Invoke the post-invocation event handler. If it requests cancellation, throw.
#pragma warning disable CS0618 // Events are deprecated
            var invokedEventArgs = kernel.OnFunctionInvoked(this, arguments, functionResult);
#pragma warning restore CS0618 // Events are deprecated

            if (invokedEventArgs is not null)
            {
                // Apply any changes from the event handlers to final result.
                functionResult = new FunctionResult(this, invokedEventArgs.ResultValue, functionResult.Culture, invokedEventArgs.Metadata ?? functionResult.Metadata);
            }

            if (invokedEventArgs?.Cancel is true)
            {
                throw new OperationCanceledException($"A {nameof(Kernel)}.{nameof(Kernel.FunctionInvoked)} event handler requested cancellation after function invocation.");
            }

            logger.LogFunctionInvokedSuccess(this.Name);
            logger.LogFunctionResultValue(functionResult);

            return functionResult;
        }
        catch (Exception ex)
        {
            HandleException(ex, logger, activity, this, kernel, arguments, functionResult, ref tags);
            throw;
        }
        finally
        {
            // Record the invocation duration metric and log the completion.
            TimeSpan duration = new((long)((Stopwatch.GetTimestamp() - startingTimestamp) * (10_000_000.0 / Stopwatch.Frequency)));
            s_invocationDuration.Record(duration.TotalSeconds, in tags);
            logger.LogFunctionComplete(duration.TotalSeconds);
        }
    }

    /// <summary>
    /// Invokes the <see cref="KernelFunction"/>.
    /// </summary>
    /// <typeparam name="TResult">Specifies the type of the result value of the function.</typeparam>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function's execution, cast to <typeparamref name="TResult"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="InvalidCastException">The function's result could not be cast to <typeparamref name="TResult"/>.</exception>
    public async Task<TResult?> InvokeAsync<TResult>(
        Kernel kernel,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default)
    {
        FunctionResult result = await this.InvokeAsync(kernel, arguments, cancellationToken).ConfigureAwait(false);
        return result.GetValue<TResult>();
    }

    /// <summary>
    /// Invokes the <see cref="KernelFunction"/> and streams its results.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="IAsyncEnumerable{T}"/> for streaming the results of the function's invocation.</returns>
    /// <remarks>
    /// The function will not be invoked until an enumerator is retrieved from the returned <see cref="IAsyncEnumerable{T}"/>
    /// and its iteration initiated via an initial call to <see cref="IAsyncEnumerator{T}.MoveNextAsync"/>.
    /// </remarks>
    public IAsyncEnumerable<StreamingKernelContent> InvokeStreamingAsync(
        Kernel kernel,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default) =>
        this.InvokeStreamingAsync<StreamingKernelContent>(kernel, arguments, cancellationToken);

    /// <summary>
    /// Invokes the <see cref="KernelFunction"/> and streams its results.
    /// </summary>
    /// <typeparam name="TResult">Specifies the type of the result values of the function.</typeparam>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="IAsyncEnumerable{TResult}"/> for streaming the results of the function's invocation.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <remarks>
    /// The function will not be invoked until an enumerator is retrieved from the returned <see cref="IAsyncEnumerable{T}"/>
    /// and its iteration initiated via an initial call to <see cref="IAsyncEnumerator{T}.MoveNextAsync"/>.
    /// </remarks>
    public async IAsyncEnumerable<TResult> InvokeStreamingAsync<TResult>(
        Kernel kernel,
        KernelArguments? arguments = null,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);

        using var activity = s_activitySource.StartActivity(this.Name);
        ILogger logger = kernel.LoggerFactory.CreateLogger(this.Name) ?? NullLogger.Instance;

        arguments ??= [];
        logger.LogFunctionStreamingInvoking(this.Name);
        logger.LogFunctionArguments(arguments);

        TagList tags = new() { { MeasurementFunctionTagName, this.Name } };
        long startingTimestamp = Stopwatch.GetTimestamp();

        try
        {
            IAsyncEnumerator<TResult> enumerator;
            try
            {
                // Quick check for cancellation after logging about function start but before doing any real work.
                cancellationToken.ThrowIfCancellationRequested();

                // Invoke pre-invocation event handler. If it requests cancellation, throw.
#pragma warning disable CS0618 // Events are deprecated
                var invokingEventArgs = kernel.OnFunctionInvoking(this, arguments);
#pragma warning restore CS0618 // Events are deprecated

                if (invokingEventArgs?.Cancel is true)
                {
                    throw new OperationCanceledException($"A {nameof(Kernel)}.{nameof(Kernel.FunctionInvoking)} event handler requested cancellation before function invocation.");
                }

                FunctionResult functionResult = new(this, culture: kernel.Culture);

                var invocationContext = await kernel.OnFunctionInvocationAsync(this, arguments, functionResult, (context) =>
                {
                    // Invoke the function and get its streaming enumerable.
                    var enumerable = this.InvokeStreamingCoreAsync<TResult>(kernel, context.Arguments, cancellationToken);

                    // Update context with enumerable as result value.
                    context.Result = new FunctionResult(this, enumerable, kernel.Culture);

                    return Task.CompletedTask;
                }, cancellationToken).ConfigureAwait(false);

                // Apply changes from the function filters to final result.
                var enumerable = invocationContext.Result.GetValue<IAsyncEnumerable<TResult>>() ?? AsyncEnumerable.Empty<TResult>();
                enumerator = enumerable.GetAsyncEnumerator(cancellationToken);

                // yielding within a try/catch isn't currently supported, so we break out of the try block
                // in order to then wrap the actual MoveNextAsync in its own try/catch and allow the yielding
                // to be lifted to be outside of the try/catch.
            }
            catch (Exception ex)
            {
                HandleException(ex, logger, activity, this, kernel, arguments, result: null, ref tags);
                throw;
            }

            // Ensure we clean up after the enumerator.
            await using (enumerator.ConfigureAwait(false))
            {
                while (true)
                {
                    try
                    {
                        // Move to the next streaming result.
                        if (!await enumerator.MoveNextAsync().ConfigureAwait(false))
                        {
                            break;
                        }
                    }
                    catch (Exception ex)
                    {
                        HandleException(ex, logger, activity, this, kernel, arguments, result: null, ref tags);
                        throw;
                    }

                    // Yield the next streaming result.
                    yield return enumerator.Current;
                }
            }
        }
        finally
        {
            // Record the streaming duration metric and log the completion.
            TimeSpan duration = new((long)((Stopwatch.GetTimestamp() - startingTimestamp) * (10_000_000.0 / Stopwatch.Frequency)));
            s_streamingDuration.Record(duration.TotalSeconds, in tags);
            logger.LogFunctionStreamingComplete(duration.TotalSeconds);
        }
    }

    /// <summary>
    /// Creates a new <see cref="KernelFunction"/> object that is a copy of the current instance
    /// but the <see cref="KernelFunctionMetadata"/> has the plugin name set.
    /// </summary>
    /// <param name="pluginName">The name of the plugin this function instance will be added to.</param>
    /// <remarks>
    /// This method should only be used to create a new instance of a <see cref="KernelFunction"/> when adding
    /// a function to a <see cref="KernelPlugin"/>.
    /// </remarks>
    public abstract KernelFunction Clone(string pluginName);

    /// <inheritdoc/>
    public override string ToString() => string.IsNullOrWhiteSpace(this.PluginName) ?
        this.Name :
        $"{this.PluginName}.{this.Name}";

    /// <summary>
    /// Invokes the <see cref="KernelFunction"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <returns>The updated context, potentially a new one if context switching is implemented.</returns>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    protected abstract ValueTask<FunctionResult> InvokeCoreAsync(
        Kernel kernel,
        KernelArguments arguments,
        CancellationToken cancellationToken);

    /// <summary>
    /// Invokes the <see cref="KernelFunction"/> and streams its results.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <returns>The updated context, potentially a new one if context switching is implemented.</returns>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    protected abstract IAsyncEnumerable<TResult> InvokeStreamingCoreAsync<TResult>(Kernel kernel,
        KernelArguments arguments,
        CancellationToken cancellationToken);

    /// <summary>Handles special-cases for exception handling when invoking a function.</summary>
    private static void HandleException(
        Exception ex,
        ILogger logger,
        Activity? activity,
        KernelFunction kernelFunction,
        Kernel kernel,
        KernelArguments arguments,
        FunctionResult? result,
        ref TagList tags)
    {
        // Log the exception and add its type to the tags that'll be included with recording the invocation duration.
        tags.Add(MeasurementErrorTagName, ex.GetType().FullName);
        activity?.SetError(ex);
        logger.LogFunctionError(ex, ex.Message);

        // If the exception is an OperationCanceledException, wrap it in a KernelFunctionCanceledException
        // in order to convey additional details about what function was canceled. This is particularly
        // important for cancellation that occurs in response to the FunctionInvoked event, in which case
        // there may be a result from a successful function invocation, and we want that result to be
        // visible to a consumer if that's needed.
        if (ex is OperationCanceledException cancelEx)
        {
            KernelFunctionCanceledException kernelEx = new(kernel, kernelFunction, arguments, result, cancelEx);
            foreach (DictionaryEntry entry in cancelEx.Data)
            {
                kernelEx.Data.Add(entry.Key, entry.Value);
            }
            throw kernelEx;
        }
    }
}

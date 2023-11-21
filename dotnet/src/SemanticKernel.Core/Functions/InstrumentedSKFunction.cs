// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>Instrumented function that surrounds the invocation of another function with logging and metrics.</summary>
internal sealed class InstrumentedSKFunction : ISKFunction
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

    /// <summary>Wrapped function instance.</summary>
    private readonly ISKFunction _function;

    /// <summary>Logger to use for logging activities.</summary>
    private readonly ILogger _logger;

    /// <summary>
    /// Initialize a new instance of the <see cref="InstrumentedSKFunction"/> class.
    /// </summary>
    /// <param name="function">Instance of <see cref="ISKFunction"/> to decorate.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public InstrumentedSKFunction(ISKFunction function, ILoggerFactory? loggerFactory = null)
    {
        this._function = function;
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(function.Name) : NullLogger.Instance;
    }

    /// <inheritdoc/>
    public string Name => this._function.Name;

    /// <inheritdoc/>
    public string Description => this._function.Description;

    /// <inheritdoc/>
    public IEnumerable<AIRequestSettings> ModelSettings => this._function.ModelSettings;

    /// <inheritdoc/>
    public Task<StreamingFunctionResult<T>> InvokeStreamingAsync<T>(
        Kernel kernel,
        SKContext context,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
            => this.StreamingInvokeWithInstrumentationAsync(
                () => this._function.InvokeStreamingAsync<T>(kernel, context, requestSettings, cancellationToken));

    #region private ================================================================================

    /// <summary>
    /// Wrapper for instrumentation to be used in multiple invocation places.
    /// </summary>
    /// <param name="func">Delegate to instrument.</param>
    private async Task<StreamingFunctionResult<T>> StreamingInvokeWithInstrumentationAsync<T>(Func<Task<StreamingFunctionResult<T>>> func)
    {
        using var activity = s_activitySource.StartActivity(this.Name);
        this._logger.LogInformation("Function invoking streaming");
        TagList tags = new() { { "sk.function.name", this.Name } };

        long startingTimestamp = Stopwatch.GetTimestamp();
        StringBuilder fullResult = new();

        var streamingResult = await func().ConfigureAwait(false);

        async IAsyncEnumerable<T> RetrieveStreamingSource()
        {
            IAsyncEnumerator<T> enumerator = streamingResult.GetAsyncEnumerator();
            bool moreChunks;
            do
            {
                T? genericChunk = default;

                try
                {
                    moreChunks = await enumerator.MoveNextAsync().ConfigureAwait(false);
                    if (moreChunks)
                    {
                        genericChunk = enumerator.Current;
                        fullResult.Append(genericChunk);
                    }
                }
                catch (Exception ex)
                {
                    if (this._logger.IsEnabled(LogLevel.Error))
                    {
                        this._logger.LogError(ex, "Function invocation failed: {Message}", ex.Message);
                        tags.Add("error.type", ex.GetType().FullName);
                    }
                    throw;
                }

                if (moreChunks && genericChunk is not null)
                {
                    yield return genericChunk;
                }
            } while (moreChunks);

            if (this._logger.IsEnabled(LogLevel.Trace))
            {
                this._logger.LogTrace("Function succeeded: {Result}", fullResult); // Sensitive data, logging as trace, disabled by default
            }
            else if (this._logger.IsEnabled(LogLevel.Information))
            {
                this._logger.LogInformation("Function succeeded.");
            }

            TimeSpan duration = new((long)((Stopwatch.GetTimestamp() - startingTimestamp) * (10_000_000.0 / Stopwatch.Frequency)));
            this._logger.LogInformation("Function invocation duration: {Duration}ms", duration.TotalMilliseconds);
            s_invocationDuration.Record(duration.TotalSeconds, in tags);
        }

        return new StreamingFunctionResult<T>(streamingResult.FunctionName, streamingResult.Context, RetrieveStreamingSource, streamingResult);
    }

    /// <inheritdoc/>
    public SKFunctionMetadata GetMetadata() =>
        this._function.GetMetadata();

    /// <inheritdoc/>
    async Task<FunctionResult> ISKFunction.InvokeAsync(Kernel kernel, SKContext context, AIRequestSettings? requestSettings, CancellationToken cancellationToken)
    {
        using var activity = s_activitySource.StartActivity(this.Name);

        this._logger.LogInformation("Function invoking");
        TagList tags = new() { { "sk.function.name", this.Name } };

        long startingTimestamp = Stopwatch.GetTimestamp();
        try
        {
            var result = await this._function.InvokeAsync(kernel, context, requestSettings, cancellationToken).ConfigureAwait(false);

            if (this._logger.IsEnabled(LogLevel.Trace))
            {
                this._logger.LogTrace("Function succeeded: {Result}", result.GetValue<object>()); // Sensitive data, logging as trace, disabled by default
            }
            else if (this._logger.IsEnabled(LogLevel.Information))
            {
                this._logger.LogInformation("Function succeeded.");
            }

            return result;
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Function invocation failed: {Message}", ex.Message);
            tags.Add("error.type", ex.GetType().FullName);
            throw;
        }
        finally
        {
            TimeSpan duration = new((long)((Stopwatch.GetTimestamp() - startingTimestamp) * (10_000_000.0 / Stopwatch.Frequency)));
            this._logger.LogInformation("Function invocation duration: {Duration}ms", duration.TotalMilliseconds);
            s_invocationDuration.Record(duration.TotalSeconds, in tags);
        }
    }

    #endregion
}

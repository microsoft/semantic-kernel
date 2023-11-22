// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.Metrics;
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
internal sealed class InstrumentedKernelFunction : KernelFunction
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
    private readonly KernelFunction _function;

    /// <summary>Logger to use for logging activities.</summary>
    private readonly ILogger _logger;

    /// <summary>
    /// Initialize a new instance of the <see cref="InstrumentedKernelFunction"/> class.
    /// </summary>
    /// <param name="function">Instance of <see cref="KernelFunction"/> to decorate.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public InstrumentedKernelFunction(KernelFunction function, ILoggerFactory? loggerFactory = null) : base(function.Name, function.Description, function.ModelSettings)
    {
        this._function = function;
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(function.Name) : NullLogger.Instance;
    }

    /// <inheritdoc/>
    public override SKFunctionMetadata GetMetadataCore() =>
        this._function.GetMetadataCore();

    /// <inheritdoc/>
    protected override async Task<FunctionResult> InvokeCoreAsync(Kernel kernel, SKContext context, AIRequestSettings? requestSettings, CancellationToken cancellationToken)
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
}

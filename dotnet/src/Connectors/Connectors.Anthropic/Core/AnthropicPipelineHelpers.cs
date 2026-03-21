// Copyright (c) Microsoft. All rights reserved.

using System;
using Anthropic;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Internal helper methods for building Anthropic M.E.AI chat client pipelines.
/// Provides consistent pipeline configuration across DI extensions and service classes.
/// </summary>
internal static class AnthropicPipelineHelpers
{
    /// <summary>
    /// Default OpenTelemetry source name for Anthropic connector telemetry.
    /// </summary>
    internal const string DefaultOpenTelemetrySourceName = "Microsoft.SemanticKernel.Connectors.Anthropic";

    /// <summary>
    /// Builds the M.E.AI chat client pipeline with SK integration and Anthropic-specific middleware.
    /// </summary>
    /// <param name="anthropicClient">The Anthropic SDK client.</param>
    /// <param name="modelId">The model identifier.</param>
    /// <param name="loggerFactory">The logger factory (can be null for no logging).</param>
    /// <param name="openTelemetrySourceName">Optional custom OpenTelemetry source name.</param>
    /// <param name="openTelemetryConfig">Optional OpenTelemetry configuration callback.</param>
    /// <returns>The configured IChatClient pipeline.</returns>
    /// <remarks>
    /// <para>
    /// The pipeline includes:
    /// <list type="bullet">
    ///   <item><description>Temperature/TopP mutual exclusion middleware (Anthropic API requirement)</description></item>
    ///   <item><description>SK function invocation filter integration via <c>UseKernelFunctionInvocation()</c></description></item>
    ///   <item><description>OpenTelemetry instrumentation via <c>UseOpenTelemetry()</c></description></item>
    ///   <item><description>Logging via <c>UseLogging()</c> (when loggerFactory is provided)</description></item>
    /// </list>
    /// </para>
    /// </remarks>
    internal static IChatClient BuildChatClientPipeline(
        AnthropicClient anthropicClient,
        string modelId,
        ILoggerFactory? loggerFactory,
        string? openTelemetrySourceName = null,
        Action<OpenTelemetryChatClient>? openTelemetryConfig = null)
    {
        var logger = loggerFactory?.CreateLogger(typeof(AnthropicPipelineHelpers));

        var builder = anthropicClient
            .AsIChatClient(modelId)
            .AsBuilder()
            // Anthropic API does not allow both temperature and top_p to be set simultaneously.
            // If both are set, clear top_p since temperature is typically the more commonly specified option.
            // Note: The Use(sharedFunc) overload returns Task (not Task<ChatResponse>). The response is
            // captured internally by AnonymousDelegatingChatClient when next() invokes the inner client.
            .Use(async (messages, options, next, cancellationToken) =>
            {
                if (options?.Temperature is not null && options.TopP is not null)
                {
                    logger?.LogWarning(
                        "Anthropic API does not support both Temperature and TopP simultaneously. " +
                        "TopP value ({TopP}) will be ignored; Temperature ({Temperature}) will be used.",
                        options.TopP,
                        options.Temperature);

                    options = options.Clone();
                    options.TopP = null;
                }

                await next(messages, options, cancellationToken).ConfigureAwait(false);
            })
            .UseKernelFunctionInvocation(loggerFactory) // SK Filter-Integration for IAutoFunctionInvocationFilter
            .UseOpenTelemetry(loggerFactory, openTelemetrySourceName ?? DefaultOpenTelemetrySourceName, openTelemetryConfig);

        if (loggerFactory is not null)
        {
            builder.UseLogging(loggerFactory);
        }

        return builder.Build();
    }
}

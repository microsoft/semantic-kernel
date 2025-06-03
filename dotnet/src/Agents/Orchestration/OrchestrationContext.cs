// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Runtime;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Provides contextual information for an orchestration operation, including topic, cancellation, logging, and response callback.
/// </summary>
public sealed class OrchestrationContext
{
    internal OrchestrationContext(
        string orchestration,
        TopicId topic,
        OrchestrationResponseCallback? responseCallback,
        ILoggerFactory loggerFactory,
        CancellationToken cancellation)
    {
        this.Orchestration = orchestration;
        this.Topic = topic;
        this.ResponseCallback = responseCallback;
        this.LoggerFactory = loggerFactory;
        this.Cancellation = cancellation;
    }

    /// <summary>
    /// Gets the name or identifier of the orchestration.
    /// </summary>
    public string Orchestration { get; }

    /// <summary>
    /// Gets the identifier associated with orchestration topic.
    /// </summary>
    /// <remarks>
    /// All orchestration actors are subscribed to this topic.
    /// </remarks>
    public TopicId Topic { get; }

    /// <summary>
    /// Gets the cancellation token that can be used to observe cancellation requests for the orchestration.
    /// </summary>
    public CancellationToken Cancellation { get; }

    /// <summary>
    /// Gets the associated logger factory for creating loggers within the orchestration context.
    /// </summary>
    public ILoggerFactory LoggerFactory { get; }

    /// <summary>
    /// Optional callback that is invoked for every agent response.
    /// </summary>
    public OrchestrationResponseCallback? ResponseCallback { get; }
}

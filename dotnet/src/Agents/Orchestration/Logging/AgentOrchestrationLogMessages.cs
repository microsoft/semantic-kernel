// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.AgentRuntime;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Extensions for logging <see cref="AgentOrchestration{TInput, TSource, TRequest, TOutput}"/>.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class AgentOrchestrationLogMessages
{
    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> awaiting the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "Registering orchestration {Orchestration} for topic: {Topic}")]
    public static partial void LogOrchestrationRegistration(
        this ILogger logger,
        string orchestration,
        TopicId topic);

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> awaiting the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Invoking orchestration {Orchestration} for topic: {Topic}")]
    public static partial void LogOrchestrationInvoke(
        this ILogger logger,
        string orchestration,
        TopicId topic);

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> awaiting the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "Yielding orchestration {Orchestration} for topic: {Topic}")]
    public static partial void LogOrchestrationYield(
        this ILogger logger,
        string orchestration,
        TopicId topic);

    /// <summary>
    /// Logs actor registration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Orchestration started: {AgentId}")]
    public static partial void LogOrchestrationStart(
        this ILogger logger,
        AgentId agentId);

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> awaiting the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Orchestration request actor initiating pattern: {AgentId}")]
    public static partial void LogOrchestrationRequestInvoke(
        this ILogger logger,
        AgentId agentId);

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> awaiting the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Error,
        Message = "Orchestration request actor failed: {AgentId}")]
    public static partial void LogOrchestrationRequestFailure(
        this ILogger logger,
        AgentId agentId,
        Exception exception);

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> awaiting the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Orchestration result actor finalizing pattern: {AgentId}")]
    public static partial void LogOrchestrationResultInvoke(
        this ILogger logger,
        AgentId agentId);

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> awaiting the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Error,
        Message = "Orchestration result actor failed: {AgentId}")]
    public static partial void LogOrchestrationResultFailure(
        this ILogger logger,
        AgentId agentId,
        Exception exception);
}

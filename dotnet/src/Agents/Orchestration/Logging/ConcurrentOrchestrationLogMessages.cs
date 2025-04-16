// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.AgentRuntime;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Extensions for logging <see cref="ConcurrentOrchestration{TInput, TOutput}"/>.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class ConcurrentOrchestrationLogMessages
{
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "Concurrent agent invoked [{AgentId}]: {Message}")]
    public static partial void LogConcurrentAgentInvoke(
        this ILogger logger,
        AgentId agentId,
        string? message);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "Concurrent agent result [{AgentId}]: {Message}")]
    public static partial void LogConcurrentAgentResult(
        this ILogger logger,
        AgentId agentId,
        string? message);

    /// <summary>
    /// Logs actor registration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Concurrent actor registered [{AgentType}]: {label}")]
    public static partial void LogConcurrentRegistration(
        this ILogger logger,
        AgentType agentType,
        string label);

    /// <summary>
    /// Logs actor registration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Concurrent actor registered [{AgentType}]: {label} #{Count}")]
    public static partial void LogConcurrentRegistration(
        this ILogger logger,
        AgentType agentType,
        string label,
        int count);

    /// <summary>
    /// Logs result capture.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Concurrent result captured [{AgentId}]: ({ResultCount} / {ExpectedCount})")]
    public static partial void LogConcurrentResultCapture(
        this ILogger logger,
        AgentId agentId,
        int resultCount,
        int expectedCount);
}

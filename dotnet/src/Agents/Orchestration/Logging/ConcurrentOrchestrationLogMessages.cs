// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;
using Microsoft.SemanticKernel.Agents.Runtime;

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
        Message = "REQUEST Concurrent agent [{AgentId}]")]
    public static partial void LogConcurrentAgentInvoke(
        this ILogger logger,
        AgentId agentId);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "RESULT Concurrent agent [{AgentId}]: {Message}")]
    public static partial void LogConcurrentAgentResult(
        this ILogger logger,
        AgentId agentId,
        string? message);

    /// <summary>
    /// Logs result capture.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "COLLECT Concurrent result [{AgentId}]: #{ResultCount} / {ExpectedCount}")]
    public static partial void LogConcurrentResultCapture(
        this ILogger logger,
        AgentId agentId,
        int resultCount,
        int expectedCount);
}

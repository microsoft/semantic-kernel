// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.AgentRuntime;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.Sequential;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Extensions for logging <see cref="SequentialOrchestration{TInput, TOutput}"/>.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class SequentialOrchestrationLogMessages
{
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "Sequential agent invoked [{AgentId}]: {Message}")]
    public static partial void LogSequentialAgentInvoke(
        this ILogger logger,
        AgentId agentId,
        string? message);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "Sequential agent result [{AgentId}]: {Message}")]
    public static partial void LogSequentialAgentResult(
        this ILogger logger,
        AgentId agentId,
        string? message);

    /// <summary>
    /// Logs actor registration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Sequential actor registered [{AgentType}]: {label}")]
    public static partial void LogSequentialRegistration(
        this ILogger logger,
        AgentType agentType,
        string label);

    /// <summary>
    /// Logs actor registration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Sequential actor registered [{AgentType}]: {label} #{Count}")]
    public static partial void LogSequentialRegistration(
        this ILogger logger,
        AgentType agentType,
        string label,
        int count);
}

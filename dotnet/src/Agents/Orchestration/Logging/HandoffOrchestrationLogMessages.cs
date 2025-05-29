// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.Handoff;
using Microsoft.SemanticKernel.Agents.Runtime;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Extensions for logging <see cref="HandoffOrchestration{TInput, TOutput}"/>.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class HandoffOrchestrationLogMessages
{
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "REQUEST Handoff agent [{AgentId}]")]
    public static partial void LogHandoffAgentInvoke(
        this ILogger logger,
        AgentId agentId);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "RESULT Handoff agent [{AgentId}]: {Message}")]
    public static partial void LogHandoffAgentResult(
        this ILogger logger,
        AgentId agentId,
        string? message);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "TOOL Handoff [{AgentId}]: {Name}")]
    public static partial void LogHandoffFunctionCall(
        this ILogger logger,
        AgentId agentId,
        string name);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "RESULT Handoff summary [{AgentId}]: {Summary}")]
    public static partial void LogHandoffSummary(
        this ILogger logger,
        AgentId agentId,
        string? summary);
}

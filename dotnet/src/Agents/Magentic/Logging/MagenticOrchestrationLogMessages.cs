// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration;
using Microsoft.SemanticKernel.Agents.Runtime;

namespace Microsoft.SemanticKernel.Agents.Magentic;

/// <summary>
/// Extensions for logging <see cref="MagenticOrchestration{TInput, TOutput}"/>.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class MagenticOrchestrationLogMessages
{
    /// <summary>
    /// Logs pattern actor registration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "REGISTER ACTOR {Orchestration} {label}: {AgentType}")]
    public static partial void LogRegisterActor(
        this ILogger logger,
        string orchestration,
        AgentType agentType,
        string label);

    /// <summary>
    /// Logs agent actor registration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "REGISTER ACTOR {Orchestration} {label} #{Count}: {AgentType}")]
    public static partial void LogRegisterActor(
        this ILogger logger,
        string orchestration,
        AgentType agentType,
        string label,
        int count);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "MAGENTIC AGENT invoked [{AgentId}]")]
    public static partial void LogMagenticAgentInvoke(
        this ILogger logger,
        AgentId agentId);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "MAGENTIC AGENT result [{AgentId}]: {Message}")]
    public static partial void LogMagenticAgentResult(
        this ILogger logger,
        AgentId agentId,
        string? message);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "MAGENTIC MANAGER initialized [{AgentId}]")]
    public static partial void LogMagenticManagerInit(
        this ILogger logger,
        AgentId agentId);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "MAGENTIC MANAGER invoked [{AgentId}]")]
    public static partial void LogMagenticManagerInvoke(
        this ILogger logger,
        AgentId agentId);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "MAGENTIC MANAGER terminate? [{AgentId}]: {Result} ({Reason})")]
    public static partial void LogMagenticManagerTerminate(
        this ILogger logger,
        AgentId agentId,
        bool result,
        string reason);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "MAGENTIC MANAGER select: {NextAgent} [{AgentId}]")]
    public static partial void LogMagenticManagerSelect(
        this ILogger logger,
        AgentId agentId,
        AgentType nextAgent);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "MAGENTIC MANAGER result [{AgentId}]: '{Result}' ({Reason})")]
    public static partial void LogMagenticManagerResult(
        this ILogger logger,
        AgentId agentId,
        string result,
        string reason);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "MAGENTIC MANAGER user-input? [{AgentId}]: {Result} ({Reason})")]
    public static partial void LogMagenticManagerInput(
        this ILogger logger,
        AgentId agentId,
        bool result,
        string reason);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "MAGENTIC AGENT user-input [{AgentId}]: {Message}")]
    public static partial void LogMagenticManagerUserInput(
        this ILogger logger,
        AgentId agentId,
        string? message);

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> timeout while awaiting the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Error,
        Message = "MAGENTIC FAILURE: {Topic}")]
    public static partial void LogMagenticManagerStatusFailure(this ILogger logger, TopicId topic, Exception exception);

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> timeout while awaiting the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Error,
        Message = "MAGENTIC MANAGER FAILURE: {Topic}")]
    public static partial void LogMagenticManagerTaskFailed(this ILogger logger, TopicId topic);

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> timeout while awaiting the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Error,
        Message = "MAGENTIC MANAGER RESET: #{ResetCount} - {Topic}")]
    public static partial void LogMagenticManagerTaskReset(
        this ILogger logger,
        TopicId topic,
        int resetCount);
}

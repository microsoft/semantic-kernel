// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;
using Microsoft.SemanticKernel.Agents.Runtime;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Extensions for logging <see cref="GroupChatOrchestration{TInput, TOutput}"/>.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class GroupChatOrchestrationLogMessages
{
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "CHAT AGENT invoked [{AgentId}]")]
    public static partial void LogChatAgentInvoke(
        this ILogger logger,
        AgentId agentId);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "CHAT AGENT result [{AgentId}]: {Message}")]
    public static partial void LogChatAgentResult(
        this ILogger logger,
        AgentId agentId,
        string? message);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "CHAT MANAGER initialized [{AgentId}]")]
    public static partial void LogChatManagerInit(
        this ILogger logger,
        AgentId agentId);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "CHAT MANAGER invoked [{AgentId}]")]
    public static partial void LogChatManagerInvoke(
        this ILogger logger,
        AgentId agentId);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "CHAT MANAGER terminate? [{AgentId}]: {Result} ({Reason})")]
    public static partial void LogChatManagerTerminate(
        this ILogger logger,
        AgentId agentId,
        bool result,
        string reason);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "CHAT MANAGER select: {NextAgent} [{AgentId}]")]
    public static partial void LogChatManagerSelect(
        this ILogger logger,
        AgentId agentId,
        AgentType nextAgent);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "CHAT MANAGER result [{AgentId}]: '{Result}' ({Reason})")]
    public static partial void LogChatManagerResult(
        this ILogger logger,
        AgentId agentId,
        string result,
        string reason);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "CHAT MANAGER user-input? [{AgentId}]: {Result} ({Reason})")]
    public static partial void LogChatManagerInput(
        this ILogger logger,
        AgentId agentId,
        bool result,
        string reason);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "CHAT AGENT user-input [{AgentId}]: {Message}")]
    public static partial void LogChatManagerUserInput(
        this ILogger logger,
        AgentId agentId,
        string? message);
}

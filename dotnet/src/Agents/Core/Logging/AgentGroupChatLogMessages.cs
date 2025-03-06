// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Extensions;

namespace Microsoft.SemanticKernel.Agents;

#pragma warning disable SYSLIB1006 // Multiple logging methods cannot use the same event id within a class

/// <summary>
/// Extensions for logging <see cref="AgentGroupChat"/> invocations.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
[Experimental("SKEXP0110")]
internal static partial class AgentGroupChatLogMessages
{
    /// <summary>
    /// Logs <see cref="AgentGroupChat"/> invoking agent (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Invoking chat: {AgentType}: {AgentId}/{AgentName}")]
    public static partial void LogAgentGroupChatInvokingAgent(
        this ILogger logger,
        string methodName,
        Type agentType,
        string agentId,
        string agentName);

    /// <summary>
    /// Logs <see cref="AgentGroupChat"/> invoking agents (started).
    /// </summary>
    private static readonly Action<ILogger, string, string, Exception?> s_logAgentGroupChatInvokingAgents =
        LoggerMessage.Define<string, string>(
            logLevel: LogLevel.Debug,
            eventId: 0,
            "[{MethodName}] Invoking chat: {Agents}");

    public static void LogAgentGroupChatInvokingAgents(
        this ILogger logger,
        string methodName,
        IEnumerable<Agent> agents)
    {
        if (logger.IsEnabled(LogLevel.Debug))
        {
            var agentsMessage = string.Join(", ", agents.Select(a => $"{a.GetType()}:{a.Id}/{a.GetDisplayName()}"));

            s_logAgentGroupChatInvokingAgents(logger, methodName, agentsMessage, null);
        }
    }

    /// <summary>
    /// Logs <see cref="AgentGroupChat"/> selecting agent (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Selecting agent: {StrategyType}.")]
    public static partial void LogAgentGroupChatSelectingAgent(
        this ILogger logger,
        string methodName,
        Type strategyType);

    /// <summary>
    /// Logs <see cref="AgentGroupChat"/> Unable to select agent.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Error,
        Message = "[{MethodName}] Unable to determine next agent.")]
    public static partial void LogAgentGroupChatNoAgentSelected(
        this ILogger logger,
        string methodName,
        Exception exception);

    /// <summary>
    /// Logs <see cref="AgentGroupChat"/> selected agent (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Agent selected {AgentType}: {AgentId}/{AgentName} by {StrategyType}")]
    public static partial void LogAgentGroupChatSelectedAgent(
        this ILogger logger,
        string methodName,
        Type agentType,
        string agentId,
        string agentName,
        Type strategyType);

    /// <summary>
    /// Logs <see cref="AgentGroupChat"/> yield chat.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Yield chat - IsComplete: {IsComplete}")]
    public static partial void LogAgentGroupChatYield(
        this ILogger logger,
        string methodName,
        bool isComplete);
}

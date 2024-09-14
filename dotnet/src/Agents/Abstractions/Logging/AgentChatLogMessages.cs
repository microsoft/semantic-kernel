// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents;

#pragma warning disable SYSLIB1006 // Multiple logging methods cannot use the same event id within a class

/// <summary>
/// Extensions for logging <see cref="AggregatorAgent"/> invocations.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class AgentChatLogMessages
{
    /// <summary>
    /// Logs retrieval of <see cref="AgentChat"/> messages.
    /// </summary>
    private static readonly Action<ILogger, string, string, string, Exception?> s_logAgentChatGetChatMessages =
        LoggerMessage.Define<string, string, string>(
            logLevel: LogLevel.Debug,
            eventId: 0,
            "[{MethodName}] Source: {MessageSourceType}/{MessageSourceId}.");
    public static void LogAgentChatGetChatMessages(
        this ILogger logger,
        string methodName,
        Agent? agent)
    {
        if (logger.IsEnabled(LogLevel.Debug))
        {
            if (null == agent)
            {
                s_logAgentChatGetChatMessages(logger, methodName, "primary", "primary", null);
            }
            else
            {
                s_logAgentChatGetChatMessages(logger, methodName, agent.GetType().Name, agent.Id, null);
            }
        }
    }

    /// <summary>
    /// Logs <see cref="AgentChat"/> adding messages (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Adding Messages: {MessageCount}.")]
    public static partial void LogAgentChatAddingMessages(
        this ILogger logger,
        string methodName,
        int messageCount);

    /// <summary>
    /// Logs <see cref="AgentChat"/> added messages (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Added Messages: {MessageCount}.")]
    public static partial void LogAgentChatAddedMessages(
        this ILogger logger,
        string methodName,
        int messageCount);

    /// <summary>
    /// Logs <see cref="AgentChat"/> invoking agent (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Invoking agent {AgentType}/{AgentId}.")]
    public static partial void LogAgentChatInvokingAgent(
        this ILogger logger,
        string methodName,
        Type agentType,
        string agentId);

    /// <summary>
    /// Logs <see cref="AgentChat"/> invoked agent message
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "[{MethodName}] Agent message {AgentType}/{AgentId}: {Message}.")]
    public static partial void LogAgentChatInvokedAgentMessage(
        this ILogger logger,
        string methodName,
        Type agentType,
        string agentId,
        ChatMessageContent message);

    /// <summary>
    /// Logs retrieval of streamed <see cref="AgentChat"/> messages.
    /// </summary>
    private static readonly Action<ILogger, string, Type, string, ChatMessageContent, Exception?> s_logAgentChatInvokedStreamingAgentMessages =
        LoggerMessage.Define<string, Type, string, ChatMessageContent>(
            logLevel: LogLevel.Debug,
            eventId: 0,
            "[{MethodName}] Agent message {AgentType}/{AgentId}: {Message}.");

    public static void LogAgentChatInvokedStreamingAgentMessages(
        this ILogger logger,
        string methodName,
        Type agentType,
        string agentId,
        IList<ChatMessageContent> messages)
    {
        if (logger.IsEnabled(LogLevel.Debug))
        {
            foreach (ChatMessageContent message in messages)
            {
                s_logAgentChatInvokedStreamingAgentMessages(logger, methodName, agentType, agentId, message, null);
            }
        }
    }

    /// <summary>
    /// Logs <see cref="AgentChat"/> invoked agent (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Invoked agent {AgentType}/{AgentId}.")]
    public static partial void LogAgentChatInvokedAgent(
        this ILogger logger,
        string methodName,
        Type agentType,
        string agentId);

    /// <summary>
    /// Logs <see cref="AgentChat"/> creating agent channel (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Creating channel for {AgentType}: {AgentId}")]
    public static partial void LogAgentChatCreatingChannel(
        this ILogger logger,
        string methodName,
        Type agentType,
        string agentId);

    /// <summary>
    /// Logs <see cref="AgentChat"/> created agent channel (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Created channel for {AgentType}: {AgentId}")]
    public static partial void LogAgentChatCreatedChannel(
        this ILogger logger,
        string methodName,
        Type agentType,
        string agentId);
}

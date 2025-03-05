// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents;

#pragma warning disable SYSLIB1006 // Multiple logging methods cannot use the same event id within a class

/// <summary>
/// Extensions for logging <see cref="ChatCompletionAgent"/> invocations.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class ChatCompletionAgentLogMessages
{
    /// <summary>
    /// Logs <see cref="ChatCompletionAgent"/> invoking agent (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Agent {AgentId}/{AgentName} Invoking service {ServiceType}.")]
    public static partial void LogAgentChatServiceInvokingAgent(
        this ILogger logger,
        string methodName,
        string agentId,
        string agentName,
        Type serviceType);

    /// <summary>
    /// Logs <see cref="ChatCompletionAgent"/> invoked agent (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Agent {AgentId}/{AgentName} Invoked service {ServiceType} with message count: {MessageCount}.")]
    public static partial void LogAgentChatServiceInvokedAgent(
        this ILogger logger,
        string methodName,
        string agentId,
        string agentName,
        Type serviceType,
        int messageCount);

    /// <summary>
    /// Logs <see cref="ChatCompletionAgent"/> invoked streaming agent (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Agent {AgentId}/{AgentName} Invoked service {ServiceType}.")]
    public static partial void LogAgentChatServiceInvokedStreamingAgent(
        this ILogger logger,
        string methodName,
        string agentId,
        string agentName,
        Type serviceType);
}

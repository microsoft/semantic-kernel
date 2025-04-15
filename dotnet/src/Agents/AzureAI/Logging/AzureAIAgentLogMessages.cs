// Copyright (c) Microsoft. All rights reserved.
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

#pragma warning disable SYSLIB1006 // Multiple logging methods cannot use the same event id within a class

/// <summary>
/// Extensions for logging <see cref="AzureAIAgent"/> invocations.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class AzureAIAgentLogMessages
{
    /// <summary>
    /// Logs <see cref="AzureAIAgent"/> creating channel (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Creating assistant thread for {ChannelType}.")]
    public static partial void LogAzureAIAgentCreatingChannel(
        this ILogger logger,
        string methodName,
        string channelType);

    /// <summary>
    /// Logs <see cref="AzureAIAgent"/> created channel (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Created assistant thread for {ChannelType}: #{ThreadId}.")]
    public static partial void LogAzureAIAgentCreatedChannel(
        this ILogger logger,
        string methodName,
        string channelType,
        string threadId);

    /// <summary>
    /// Logs <see cref="AzureAIAgent"/> restoring serialized channel (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Restoring assistant channel for {ChannelType}: #{ThreadId}.")]
    public static partial void LogAzureAIAgentRestoringChannel(
        this ILogger logger,
        string methodName,
        string channelType,
        string threadId);

    /// <summary>
    /// Logs <see cref="AzureAIAgent"/> restored serialized channel (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Restored assistant channel for {ChannelType}: #{ThreadId}.")]
    public static partial void LogAzureAIAgentRestoredChannel(
        this ILogger logger,
        string methodName,
        string channelType,
        string threadId);
}

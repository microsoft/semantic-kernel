// Copyright (c) Microsoft. All rights reserved.
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

#pragma warning disable SYSLIB1006 // Multiple logging methods cannot use the same event id within a class

/// <summary>
/// Extensions for logging <see cref="AggregatorAgent"/> invocations.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class OpenAIAssistantAgentLogMessages
{
    /// <summary>
    /// Logs <see cref="OpenAIAssistantAgent"/> creating channel (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Creating assistant thread for {ChannelType}.")]
    public static partial void LogOpenAIAssistantAgentCreatingChannel(
        this ILogger logger,
        string methodName,
        string channelType);

    /// <summary>
    /// Logs <see cref="OpenAIAssistantAgent"/> created channel (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Created assistant thread for {ChannelType}: #{ThreadId}.")]
    public static partial void LogOpenAIAssistantAgentCreatedChannel(
        this ILogger logger,
        string methodName,
        string channelType,
        string threadId);
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head

    /// <summary>
    /// Logs <see cref="OpenAIAssistantAgent"/> restoring serialized channel (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Restoring assistant channel for {ChannelType}: #{ThreadId}.")]
    public static partial void LogOpenAIAssistantAgentRestoringChannel(
        this ILogger logger,
        string methodName,
        string channelType,
        string threadId);

    /// <summary>
    /// Logs <see cref="OpenAIAssistantAgent"/> restored serialized channel (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Restored assistant channel for {ChannelType}: #{ThreadId}.")]
    public static partial void LogOpenAIAssistantAgentRestoredChannel(
        this ILogger logger,
        string methodName,
        string channelType,
        string threadId);
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
}

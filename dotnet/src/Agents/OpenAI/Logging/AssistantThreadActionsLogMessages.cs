// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

#pragma warning disable SYSLIB1006 // Multiple logging methods cannot use the same event id within a class

/// <summary>
/// Extensions for logging <see cref="AssistantThreadActions"/>.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class AssistantThreadActionsLogMessages
{
    /// <summary>
    /// Logs <see cref="AssistantThreadActions"/> creating run (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Creating run for thread: {ThreadId}.")]
    public static partial void LogOpenAIAssistantCreatingRun(
        this ILogger logger,
        string methodName,
        string threadId);

    /// <summary>
    /// Logs <see cref="AssistantThreadActions"/> created run (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Created run for thread: {RunId}/{ThreadId}.")]
    public static partial void LogOpenAIAssistantCreatedRun(
        this ILogger logger,
        string methodName,
        string runId,
        string threadId);

    /// <summary>
    /// Logs <see cref="AssistantThreadActions"/> completed run (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Completed run for thread: {RunId}/{ThreadId}.")]
    public static partial void LogOpenAIAssistantCompletedRun(
        this ILogger logger,
        string methodName,
        string runId,
        string threadId);

    /// <summary>
    /// Logs <see cref="AssistantThreadActions"/> processing run steps (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Processing run steps for thread: {RunId}/{ThreadId}.")]
    public static partial void LogOpenAIAssistantProcessingRunSteps(
        this ILogger logger,
        string methodName,
        string runId,
        string threadId);

    /// <summary>
    /// Logs <see cref="AssistantThreadActions"/> processed run steps (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Processed #{stepCount} run steps: {RunId}/{ThreadId}.")]
    public static partial void LogOpenAIAssistantProcessedRunSteps(
        this ILogger logger,
        string methodName,
        int stepCount,
        string runId,
        string threadId);

    /// <summary>
    /// Logs <see cref="AssistantThreadActions"/> processing run messages (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Processing run messages for thread: {RunId}/{ThreadId}.")]
    public static partial void LogOpenAIAssistantProcessingRunMessages(
        this ILogger logger,
        string methodName,
        string runId,
        string threadId);

    /// <summary>
    /// Logs <see cref="AssistantThreadActions"/> processed run messages (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Processed #{MessageCount} run steps: {RunId}/{ThreadId}.")]
    public static partial void LogOpenAIAssistantProcessedRunMessages(
        this ILogger logger,
        string methodName,
        int messageCount,
        string runId,
        string threadId);

    /// <summary>
    /// Logs <see cref="AssistantThreadActions"/> polling run status (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Polling run status for thread: {RunId}/{ThreadId}.")]
    public static partial void LogOpenAIAssistantPollingRunStatus(
        this ILogger logger,
        string methodName,
        string runId,
        string threadId);

    /// <summary>
    /// Logs <see cref="AssistantThreadActions"/> polled run status (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Run status is {RunStatus}: {RunId}/{ThreadId}.")]
    public static partial void LogOpenAIAssistantPolledRunStatus(
        this ILogger logger,
        string methodName,
        RunStatus runStatus,
        string runId,
        string threadId);

    /// <summary>
    /// Logs <see cref="AssistantThreadActions"/> polled run status (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Warning,
        Message = "[{MethodName}] Unknown annotation '{Type}': {RunId}/{ThreadId}.")]
    public static partial void LogOpenAIAssistantUnknownAnnotation(
        this ILogger logger,
        string methodName,
        string runId,
        string threadId,
        Type type);
}

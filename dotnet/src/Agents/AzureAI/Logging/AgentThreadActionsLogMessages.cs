// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Diagnostics.CodeAnalysis;
using Azure.AI.Agents.Persistent;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.AzureAI.Internal;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

#pragma warning disable SYSLIB1006 // Multiple logging methods cannot use the same event id within a class

/// <summary>
/// Extensions for logging <see cref="AgentThreadActions"/>.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class AgentThreadActionsLogMessages
{
    /// <summary>
    /// Logs <see cref="AgentThreadActions"/> creating run (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Creating run for thread: {ThreadId}.")]
    public static partial void LogAzureAIAgentCreatingRun(
        this ILogger logger,
        string methodName,
        string threadId);

    /// <summary>
    /// Logs <see cref="AgentThreadActions"/> created run (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Created run for thread: {RunId}/{ThreadId}.")]
    public static partial void LogAzureAIAgentCreatedRun(
        this ILogger logger,
        string methodName,
        string runId,
        string threadId);

    /// <summary>
    /// Logs <see cref="AgentThreadActions"/> completed run (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Completed run for thread: {RunId}/{ThreadId}.")]
    public static partial void LogAzureAIAgentCompletedRun(
        this ILogger logger,
        string methodName,
        string runId,
        string threadId);

    /// <summary>
    /// Logs <see cref="AgentThreadActions"/> processing run steps (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Processing run steps for thread: {RunId}/{ThreadId}.")]
    public static partial void LogAzureAIAgentProcessingRunSteps(
        this ILogger logger,
        string methodName,
        string runId,
        string threadId);

    /// <summary>
    /// Logs <see cref="AgentThreadActions"/> processed run steps (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Processed #{stepCount} run steps: {RunId}/{ThreadId}.")]
    public static partial void LogAzureAIAgentProcessedRunSteps(
        this ILogger logger,
        string methodName,
        int stepCount,
        string runId,
        string threadId);

    /// <summary>
    /// Logs <see cref="AgentThreadActions"/> processing run messages (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Processing run messages for thread: {RunId}/{ThreadId}.")]
    public static partial void LogAzureAIAgentProcessingRunMessages(
        this ILogger logger,
        string methodName,
        string runId,
        string threadId);

    /// <summary>
    /// Logs <see cref="AgentThreadActions"/> processed run messages (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Processed #{MessageCount} run steps: {RunId}/{ThreadId}.")]
    public static partial void LogAzureAIAgentProcessedRunMessages(
        this ILogger logger,
        string methodName,
        int messageCount,
        string runId,
        string threadId);

    /// <summary>
    /// Logs <see cref="AgentThreadActions"/> polling run status (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Polling run status for thread: {RunId}/{ThreadId}.")]
    public static partial void LogAzureAIAgentPollingRunStatus(
        this ILogger logger,
        string methodName,
        string runId,
        string threadId);

    /// <summary>
    /// Logs <see cref="AgentThreadActions"/> polled run status (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Run status is {RunStatus}: {RunId}/{ThreadId}.")]
    public static partial void LogAzureAIAgentPolledRunStatus(
        this ILogger logger,
        string methodName,
        RunStatus runStatus,
        string runId,
        string threadId);

    /// <summary>
    /// Logs <see cref="AgentThreadActions"/> polled run status (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Warning,
        Message = "[{MethodName}] Unknown annotation '{Type}': {RunId}/{ThreadId}.")]
    public static partial void LogAzureAIAgentUnknownAnnotation(
        this ILogger logger,
        string methodName,
        string runId,
        string threadId,
        Type type);
}

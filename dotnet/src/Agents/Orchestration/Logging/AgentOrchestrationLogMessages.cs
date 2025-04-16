// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.AgentRuntime;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Extensions for logging <see cref="AgentOrchestration{TInput, TSource, TRequest, TOutput}"/>.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class AgentOrchestrationLogMessages
{
    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> awaiting the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "REGISTER {Orchestration} Start: {Topic}")]
    public static partial void LogOrchestrationRegistrationStart(
        this ILogger logger,
        string orchestration,
        TopicId topic);

    /// <summary>
    /// Logs actor registration.
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
    /// Logs actor registration.
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

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> awaiting the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "REGISTER {Orchestration} Complete: {Topic}")]
    public static partial void LogOrchestrationRegistrationDone(
        this ILogger logger,
        string orchestration,
        TopicId topic);

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> orchestration invocation.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "INVOKE {Orchestration}: {Topic}")]
    public static partial void LogOrchestrationInvoke(
        this ILogger logger,
        string orchestration,
        TopicId topic);

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> that the orchestration
    /// has started successfully and yielded control back to the caller.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "YIELD {Orchestration}: {Topic}")]
    public static partial void LogOrchestrationYield(
        this ILogger logger,
        string orchestration,
        TopicId topic);

    /// <summary>
    /// Logs the start of the outer orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "START {Orchestration}: {AgentId}")]
    public static partial void LogOrchestrationStart(
        this ILogger logger,
        string orchestration,
        AgentId agentId);

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "INIT {Orchestration}: {AgentId}")]
    public static partial void LogOrchestrationRequestInvoke(
        this ILogger logger,
        string orchestration,
        AgentId agentId);

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Error,
        Message = "{Orchestration} request failed: {AgentId}")]
    public static partial void LogOrchestrationRequestFailure(
        this ILogger logger,
        string orchestration,
        AgentId agentId,
        Exception exception);

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "EXIT {Orchestration}: {AgentId}")]
    public static partial void LogOrchestrationResultInvoke(
        this ILogger logger,
        string orchestration,
        AgentId agentId);

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Error,
        Message = "{Orchestration} result failed: {AgentId}")]
    public static partial void LogOrchestrationResultFailure(
        this ILogger logger,
        string orchestration,
        AgentId agentId,
        Exception exception);
}

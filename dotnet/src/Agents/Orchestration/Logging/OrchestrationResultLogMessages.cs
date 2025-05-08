// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Runtime;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Extensions for logging <see cref="OrchestrationResult{TValue}"/>.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class OrchestrationResultLogMessages
{
    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> awaiting the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "AWAIT {Orchestration}: {Topic}")]
    public static partial void LogOrchestrationResultAwait(
        this ILogger logger,
        string orchestration,
        TopicId topic);

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> timeout while awaiting the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Error,
        Message = "TIMEOUT {Orchestration}: {Topic}")]
    public static partial void LogOrchestrationResultTimeout(
        this ILogger logger,
        string orchestration,
        TopicId topic);

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> cancelled the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Error,
        Message = "CANCELLED {Orchestration}: {Topic}")]
    public static partial void LogOrchestrationResultCancelled(
        this ILogger logger,
        string orchestration,
        TopicId topic);

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> the awaited the orchestration has completed.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "COMPLETE {Orchestration}: {Topic}")]
    public static partial void LogOrchestrationResultComplete(
        this ILogger logger,
        string orchestration,
        TopicId topic);
}

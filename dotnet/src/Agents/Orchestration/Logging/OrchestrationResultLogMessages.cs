// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.AgentRuntime;
using Microsoft.Extensions.Logging;

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
        Message = "Awaiting orchestration result for topic: {Topic}")]
    public static partial void LogOrchestrationResultAwait(
        this ILogger logger,
        TopicId topic);

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> awaiting the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Error,
        Message = "Orchestration result timeout for topic: {Topic}")]
    public static partial void LogOrchestrationResultTimeout(
        this ILogger logger,
        TopicId topic);

    /// <summary>
    /// Logs <see cref="OrchestrationResult{TValue}"/> awaiting the orchestration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace,
        Message = "Orchestration result completed for topic: {Topic}")]
    public static partial void LogOrchestrationResultComplete(
        this ILogger logger,
        TopicId topic);
}

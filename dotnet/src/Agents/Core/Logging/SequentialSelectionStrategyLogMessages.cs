// Copyright (c) Microsoft. All rights reserved.
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents.Chat;

#pragma warning disable SYSLIB1006 // Multiple logging methods cannot use the same event id within a class

/// <summary>
/// Extensions for logging <see cref="SequentialSelectionStrategy"/> invocations.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
[Experimental("SKEXP0110")]
internal static partial class SequentialSelectionStrategyLogMessages
{
    /// <summary>
    /// Logs <see cref="SequentialSelectionStrategy"/> selected agent (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Selected agent ({AgentIndex} / {AgentCount}): {AgentId}/{AgentName}")]
    public static partial void LogSequentialSelectionStrategySelectedAgent(
        this ILogger logger,
        string methodName,
        int agentIndex,
        int agentCount,
        string agentId,
        string agentName);
}

// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.AgentRuntime;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Extensions for logging <see cref="GroupChatOrchestration{TInput, TOutput}"/>.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class GroupChatOrchestrationLogMessages
{
    /// <summary>
    /// Logs actor registration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "GroupChat actor registered [{AgentType}]: {label}")]
    public static partial void LogGroupChatRegistration(
        this ILogger logger,
        AgentType agentType,
        string label);

    /// <summary>
    /// Logs actor registration.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "GroupChat actor registered [{AgentType}]: {label} #{Count}")]
    public static partial void LogGroupChatRegistration(
        this ILogger logger,
        AgentType agentType,
        string label,
        int count);
}

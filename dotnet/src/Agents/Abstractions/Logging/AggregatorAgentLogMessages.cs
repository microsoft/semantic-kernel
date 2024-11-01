﻿// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents;

#pragma warning disable SYSLIB1006 // Multiple logging methods cannot use the same event id within a class

/// <summary>
/// Extensions for logging <see cref="AggregatorAgent"/> invocations.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class AggregatorAgentLogMessages
{
    /// <summary>
    /// Logs <see cref="AggregatorAgent"/> creating channel (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Creating channel {ChannelType}.")]
    public static partial void LogAggregatorAgentCreatingChannel(
        this ILogger logger,
        string methodName,
        string channelType);

    /// <summary>
    /// Logs <see cref="AggregatorAgent"/> created channel (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Created channel {ChannelType} ({ChannelMode}) with: {AgentChatType}.")]
    public static partial void LogAggregatorAgentCreatedChannel(
        this ILogger logger,
        string methodName,
        string channelType,
        AggregatorMode channelMode,
        Type agentChatType);
}

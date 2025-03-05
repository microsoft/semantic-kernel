// Copyright (c) Microsoft. All rights reserved.
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents.Chat;

#pragma warning disable SYSLIB1006 // Multiple logging methods cannot use the same event id within a class

/// <summary>
/// Extensions for logging <see cref="AggregatorTerminationStrategy"/> invocations.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
[Experimental("SKEXP0110")]
internal static partial class AggregatorTerminationStrategyLogMessages
{
    /// <summary>
    /// Logs <see cref="AggregatorTerminationStrategy"/> invoking agent (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Evaluating termination for {StrategyCount} strategies: {AggregationMode}")]
    public static partial void LogAggregatorTerminationStrategyEvaluating(
        this ILogger logger,
        string methodName,
        int strategyCount,
        AggregateTerminationCondition aggregationMode);
}

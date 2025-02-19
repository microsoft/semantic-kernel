// Copyright (c) Microsoft. All rights reserved.
using System.Diagnostics.CodeAnalysis;
using System.Text.RegularExpressions;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents.Chat;

#pragma warning disable SYSLIB1006 // Multiple logging methods cannot use the same event id within a class

/// <summary>
/// Extensions for logging <see cref="RegexTerminationStrategy"/> invocations.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
[Experimental("SKEXP0110")]
internal static partial class RegExTerminationStrategyLogMessages
{
    /// <summary>
    /// Logs <see cref="RegexTerminationStrategy"/> begin evaluation (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Evaluating expressions: {ExpressionCount}")]
    public static partial void LogRegexTerminationStrategyEvaluating(
        this ILogger logger,
        string methodName,
        int expressionCount);

    /// <summary>
    /// Logs <see cref="RegexTerminationStrategy"/> evaluating expression (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Evaluating expression: {Expression}")]
    public static partial void LogRegexTerminationStrategyEvaluatingExpression(
        this ILogger logger,
        string methodName,
        Regex expression);

    /// <summary>
    /// Logs <see cref="RegexTerminationStrategy"/> expression matched (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Expression matched: {Expression}")]
    public static partial void LogRegexTerminationStrategyMatchedExpression(
        this ILogger logger,
        string methodName,
        Regex expression);

    /// <summary>
    /// Logs <see cref="RegexTerminationStrategy"/> no match (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] No expression matched.")]
    public static partial void LogRegexTerminationStrategyNoMatch(
        this ILogger logger,
        string methodName);
}

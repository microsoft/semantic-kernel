// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents.IntentTriage.Logging;

#pragma warning disable SYSLIB1006 // Multiple logging methods cannot use the same event id within a class

/// <summary>
/// Extensions for logging <see cref="LanguagePlugin"/> invocations.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
internal static partial class LanguagePluginLogMessages
{
    /// <summary>
    /// Logs <see cref="LanguagePlugin.AnalyzeMessageAsync"/> (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[LanguagePlugin] Invoking AnalyzeMessage: {endpoint}")]
    public static partial void LogAnalyzeInvoking(
        this ILogger logger,
        Uri endpoint);

    /// <summary>
    /// Logs <see cref="LanguagePlugin.AnalyzeMessageAsync"/> (completed).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[LanguagePlugin] Invoked AnalyzeMessage: {result} ({confidence})")]
    public static partial void LogAnalyzeInvoked(
        this ILogger logger,
        string? result,
        decimal confidence);

    /// <summary>
    /// Logs <see cref="LanguagePlugin.QueryKnowledgeBaseAsync"/> (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[LanguagePlugin] Invoking QueryKnowledgeBase: {endpoint}")]
    public static partial void LogQueryInvoking(
        this ILogger logger,
        Uri endpoint);

    /// <summary>
    /// Logs <see cref="LanguagePlugin.QueryKnowledgeBaseAsync"/> (completed).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[LanguagePlugin] Invoked QueryKnowledgeBase: {result} ({confidence})")]
    public static partial void LogQueryInvoked(
        this ILogger logger,
        string? result,
        decimal confidence);
}

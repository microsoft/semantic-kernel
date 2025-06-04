// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Connectors.FunctionCalling;

[ExcludeFromCodeCoverage]
internal static partial class FunctionCallsProcessorLoggingExtensions
{
    /// <summary>
    /// Action to log the <see cref="FunctionChoiceBehaviorConfiguration"/>.
    /// </summary>
    private static readonly Action<ILogger, string, bool, bool, bool?, string, Exception?> s_logFunctionChoiceBehaviorConfiguration =
        LoggerMessage.Define<string, bool, bool, bool?, string>(
            logLevel: LogLevel.Debug,
            eventId: 0,
            "Function choice behavior configuration: Choice:{Choice}, AutoInvoke:{AutoInvoke}, AllowConcurrentInvocation:{AllowConcurrentInvocation}, AllowParallelCalls:{AllowParallelCalls} Functions:{Functions}");

    /// <summary>
    /// Action to log function calls.
    /// </summary>
    private static readonly Action<ILogger, string, Exception?> s_logFunctionCalls =
        LoggerMessage.Define<string>(
            logLevel: LogLevel.Debug,
            eventId: 0,
            "Function calls: {Calls}");

    /// <summary>
    /// Action to log auto function invocation filter context.
    /// </summary>
    private static readonly Action<ILogger, string, string?, bool, int, int, int, Exception?> s_logAutoFunctionInvocationFilterContext =
        LoggerMessage.Define<string, string?, bool, int, int, int>(
            logLevel: LogLevel.Debug,
            eventId: 0,
            "Auto function invocation filter context: Name:{Name}, Id:{Id}, IsStreaming:{IsStreaming} FunctionSequenceIndex:{FunctionSequenceIndex}, RequestSequenceIndex:{RequestSequenceIndex}, FunctionCount:{FunctionCount}");

    /// <summary>
    /// Action to log auto function invocation filter termination.
    /// </summary>
    private static readonly Action<ILogger, string, string?, Exception?> s_logAutoFunctionInvocationFilterTermination =
        LoggerMessage.Define<string, string?>(
            logLevel: LogLevel.Debug,
            eventId: 0,
            "Auto function invocation filter requested termination: Name:{Name}, Id:{Id}");

    /// <summary>
    /// Logs <see cref="FunctionChoiceBehaviorConfiguration"/>.
    /// </summary>
    public static void LogFunctionChoiceBehaviorConfiguration(this ILogger logger, FunctionChoiceBehaviorConfiguration configuration)
    {
        if (logger.IsEnabled(LogLevel.Debug))
        {
            var functionsLog = (configuration.Functions != null && configuration.Functions.Any())
                ? string.Join(", ", configuration.Functions.Select(f => FunctionName.ToFullyQualifiedName(f.Name, f.PluginName)))
                : "None (Function calling is disabled)";

            s_logFunctionChoiceBehaviorConfiguration(
                logger,
                configuration.Choice.Label,
                configuration.AutoInvoke,
                configuration.Options.AllowConcurrentInvocation,
                configuration.Options.AllowParallelCalls,
                functionsLog,
                null);
        }
    }

    /// <summary>
    /// Logs function calls.
    /// </summary>
    public static void LogFunctionCalls(this ILogger logger, FunctionCallContent[] functionCalls)
    {
        if (logger.IsEnabled(LogLevel.Debug))
        {
            s_logFunctionCalls(
                logger,
                string.Join(", ", functionCalls.Select(call => $"{FunctionName.ToFullyQualifiedName(call.FunctionName, call.PluginName)} [Id: {call.Id}]")),
                null
            );
        }
    }

    /// <summary>
    /// Logs the <see cref="AutoFunctionInvocationContext"/>.
    /// </summary>
    public static void LogAutoFunctionInvocationFilterContext(this ILogger logger, AutoFunctionInvocationContext context)
    {
        if (logger.IsEnabled(LogLevel.Debug))
        {
            var fqn = FunctionName.ToFullyQualifiedName(context.Function.Name, context.Function.PluginName);

            s_logAutoFunctionInvocationFilterContext(
                    logger,
                    fqn,
                    context.ToolCallId,
                    context.IsStreaming,
                    context.FunctionSequenceIndex,
                    context.RequestSequenceIndex,
                    context.FunctionCount,
                    null);
        }
    }

    /// <summary>
    /// Logs the auto function invocation process termination.
    /// </summary>
    public static void LogAutoFunctionInvocationProcessTermination(this ILogger logger, AutoFunctionInvocationContext context)
    {
        if (logger.IsEnabled(LogLevel.Debug))
        {
            var fqn = FunctionName.ToFullyQualifiedName(context.Function.Name, context.Function.PluginName);

            s_logAutoFunctionInvocationFilterTermination(logger, fqn, context.ToolCallId, null);
        }
    }

    /// <summary>
    /// Logs function call request failure.
    /// </summary>
    public static void LogFunctionCallRequestFailure(this ILogger logger, FunctionCallContent functionCall, string error)
    {
        if (logger.IsEnabled(LogLevel.Debug))
        {
            var fqn = FunctionName.ToFullyQualifiedName(functionCall.FunctionName, functionCall.PluginName);

            logger.LogDebug("Function call request failed: Name:{Name}, Id:{Id}", fqn, functionCall.Id);
        }

        // Log error at trace level only because it may contain sensitive information.
        if (logger.IsEnabled(LogLevel.Trace))
        {
            var fqn = FunctionName.ToFullyQualifiedName(functionCall.FunctionName, functionCall.PluginName);

            logger.LogTrace("Function call request failed: Name:{Name}, Id:{Id}, Error:{Error}", fqn, functionCall.Id, error);
        }
    }

    [LoggerMessage(EventId = 0, Level = LogLevel.Debug, Message = "The maximum limit of {MaxNumberOfAutoInvocations} auto invocations per user request has been reached. Auto invocation is now disabled.")]
    public static partial void LogMaximumNumberOfAutoInvocationsPerUserRequestReached(this ILogger logger, int maxNumberOfAutoInvocations);

    [LoggerMessage(EventId = 0, Level = LogLevel.Debug, Message = "The maximum limit of {MaxNumberOfInflightAutoInvocations} in-flight auto invocations has been reached. Auto invocation is now disabled.")]
    public static partial void LogMaximumNumberOfInFlightAutoInvocationsReached(this ILogger logger, int maxNumberOfInflightAutoInvocations);
}

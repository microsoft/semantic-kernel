// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable SYSLIB1006 // Multiple logging methods cannot use the same event id within a class

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization.Metadata;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extensions for logging <see cref="KernelFunction"/> invocations.
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </summary>
internal static partial class KernelFunctionLogMessages
{
    /// <summary>
    /// Logs invocation of a <see cref="KernelFunction"/>.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Function {PluginName}-{FunctionName} invoking.")]
    public static partial void LogFunctionInvoking(
        this ILogger logger,
        string? pluginName,
        string functionName);

    /// <summary>
    /// Logs arguments of a <see cref="KernelFunction"/>.
    /// The action provides the benefit of caching the template parsing result for better performance.
    /// And the public method is a helper to serialize the arguments.
    /// </summary>
    private static readonly Action<ILogger, string?, string, string, Exception?> s_logFunctionArguments =
        LoggerMessage.Define<string?, string, string>(
            logLevel: LogLevel.Trace,   // Sensitive data, logging as trace, disabled by default
            eventId: 0,
            "Function {PluginName}-{FunctionName} arguments: {Arguments}");

    [RequiresUnreferencedCode("Uses reflection to serialize function arguments, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to serialize the function arguments, making it incompatible with AOT scenarios.")]
    public static void LogFunctionArguments(this ILogger logger, string? pluginName, string functionName, KernelArguments arguments)
    {
        LogFunctionArgumentsInternal(logger, pluginName, functionName, arguments);
    }

    /// <summary>
    /// Logs arguments of a <see cref="KernelFunction"/>.
    /// </summary>
    [UnconditionalSuppressMessage("Trimming", "IL2026:Members annotated with 'RequiresUnreferencedCodeAttribute' require dynamic access otherwise can break functionality when trimming application code", Justification = "This method is AOT safe.")]
    [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "This method is AOT safe.")]
    public static void LogFunctionArguments(this ILogger logger, string? pluginName, string functionName, KernelArguments arguments, JsonSerializerOptions jsonSerializerOptions)
    {
        LogFunctionArgumentsInternal(logger, pluginName, functionName, arguments, jsonSerializerOptions);
    }

    /// <summary>
    /// Logs arguments of a <see cref="KernelFunction"/>.
    /// </summary>
    [RequiresUnreferencedCode("Uses reflection, if no JOSs are supplied, to serialize function arguments, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection, if no JOSs are supplied, to serialize function arguments, making it incompatible with AOT scenarios.")]
    private static void LogFunctionArgumentsInternal(this ILogger logger, string? pluginName, string functionName, KernelArguments arguments, JsonSerializerOptions? jsonSerializerOptions = null)
    {
        if (logger.IsEnabled(LogLevel.Trace))
        {
            try
            {
                string jsonString;

                if (jsonSerializerOptions is not null)
                {
                    JsonTypeInfo<KernelArguments> typeInfo = (JsonTypeInfo<KernelArguments>)jsonSerializerOptions.GetTypeInfo(typeof(KernelArguments));
                    jsonString = JsonSerializer.Serialize(arguments, typeInfo);
                }
                else
                {
                    jsonString = JsonSerializer.Serialize(arguments);
                }

                s_logFunctionArguments(logger, pluginName, functionName, jsonString, null);
            }
            catch (NotSupportedException ex)
            {
                s_logFunctionArguments(logger, pluginName, functionName, "Failed to serialize arguments to Json", ex);
            }
        }
    }

    /// <summary>
    /// Logs successful invocation of a <see cref="KernelFunction"/>.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Function {PluginName}-{FunctionName} succeeded.")]
    public static partial void LogFunctionInvokedSuccess(this ILogger logger, string? pluginName, string functionName);

    /// <summary>
    /// Logs result of a <see cref="KernelFunction"/>.
    /// The action provides the benefit of caching the template parsing result for better performance.
    /// And the public method is a helper to serialize the result.
    /// </summary>
    private static readonly Action<ILogger, string?, string, string, Exception?> s_logFunctionResultValue =
        LoggerMessage.Define<string?, string, string>(
            logLevel: LogLevel.Trace,   // Sensitive data, logging as trace, disabled by default
            eventId: 0,
            "Function {PluginName}-{FunctionName} result: {ResultValue}");
    [RequiresUnreferencedCode("Uses reflection to serialize function result, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to serialize the function result, making it incompatible with AOT scenarios.")]
    public static void LogFunctionResultValue(this ILogger logger, string? pluginName, string functionName, FunctionResult? resultValue)
    {
        LogFunctionResultValueInternal(logger, pluginName, functionName, resultValue);
    }

    /// <summary>
    /// Logs result of a <see cref="KernelFunction"/>.
    /// The action provides the benefit of caching the template parsing result for better performance.
    /// And the public method is a helper to serialize the result.
    /// </summary>
    [UnconditionalSuppressMessage("Trimming", "IL2026:Members annotated with 'RequiresUnreferencedCodeAttribute' require dynamic access otherwise can break functionality when trimming application code", Justification = "This method is AOT safe.")]
    [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "This method is AOT safe.")]
    public static void LogFunctionResultValue(this ILogger logger, string? pluginName, string functionName, FunctionResult? resultValue, JsonSerializerOptions jsonSerializerOptions)
    {
        LogFunctionResultValueInternal(logger, pluginName, functionName, resultValue, jsonSerializerOptions);
    }

    [SuppressMessage("Design", "CA1031:Do not catch general exception types", Justification = "By design. See comment below.")]
    [RequiresUnreferencedCode("Uses reflection, if no JOSs are supplied, to serialize function arguments, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection, if no JOSs are supplied, to serialize function arguments, making it incompatible with AOT scenarios.")]
    private static void LogFunctionResultValueInternal(this ILogger logger, string? pluginName, string functionName, FunctionResult? resultValue, JsonSerializerOptions? jsonSerializerOptions = null)
    {
        if (logger.IsEnabled(LogLevel.Trace))
        {
            // Attempt to convert the result value to string using the GetValue heuristic
            try
            {
                s_logFunctionResultValue(logger, pluginName, functionName, resultValue?.GetValue<string>() ?? string.Empty, null);
                return;
            }
            catch { }

            // Falling back to Json serialization
            try
            {
                string jsonString;

                if (jsonSerializerOptions is not null)
                {
                    JsonTypeInfo<object?> typeInfo = (JsonTypeInfo<object?>)jsonSerializerOptions.GetTypeInfo(typeof(object));
                    jsonString = JsonSerializer.Serialize(resultValue?.Value, typeInfo);
                }
                else
                {
                    jsonString = JsonSerializer.Serialize(resultValue?.Value);
                }

                s_logFunctionResultValue(logger, pluginName, functionName, jsonString, null);
            }
            catch (NotSupportedException ex)
            {
                s_logFunctionResultValue(logger, pluginName, functionName, "Failed to log function result value", ex);
            }
        }
    }

    /// <summary>
    /// Logs <see cref="KernelFunction"/> error.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Error,
        Message = "Function {PluginName}-{FunctionName} failed. Error: {Message}")]
    public static partial void LogFunctionError(
        this ILogger logger,
        string? pluginName,
        string functionName,
        Exception exception,
        string message);

    /// <summary>
    /// Logs <see cref="KernelFunction"/> complete.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Function {PluginName}-{FunctionName} completed. Duration: {Duration}s")]
    public static partial void LogFunctionComplete(
        this ILogger logger,
        string? pluginName,
        string functionName,
        double duration);

    /// <summary>
    /// Logs streaming invocation of a <see cref="KernelFunction"/>.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Function {PluginName}-{FunctionName} streaming.")]
    public static partial void LogFunctionStreamingInvoking(
        this ILogger logger,
        string? pluginName,
        string functionName);

    /// <summary>
    /// Logs <see cref="KernelFunction"/> streaming complete.
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Function {PluginName}-{FunctionName} streaming completed. Duration: {Duration}s.")]
    public static partial void LogFunctionStreamingComplete(
        this ILogger logger,
        string? pluginName,
        string functionName,
        double duration);
}

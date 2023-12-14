// Copyright (c) Microsoft. All rights reserved.

using System;
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
        Level = LogLevel.Trace, // Sensitive data, logging as trace, disabled by default
        Message = "Function {FunctionName} invoking. Arguments: {Arguments}.")]
    public static partial void LogFunctionInvokingWithArguments(
        this ILogger logger,
        string functionName,
        KernelArguments arguments);

    /// <summary>
    /// Logs cancellation of a <see cref="KernelFunction"/>.
    /// </summary>
    [LoggerMessage(
        EventId = 1,
        Level = LogLevel.Information,
        Message = "Function canceled prior to invocation.")]
    public static partial void LogFunctionCanceledPriorToInvoking(this ILogger logger);

    /// <summary>
    /// Logs successful invocation of a <see cref="KernelFunction"/>.
    /// </summary>
    [LoggerMessage(
        EventId = 2,
        Level = LogLevel.Trace, // Sensitive data, logging as trace, disabled by default
        Message = "Function succeeded. Result: {Result}")]
    public static partial void LogFunctionInvokedSuccess(this ILogger logger, object? result);

    /// <summary>
    /// Logs <see cref="KernelFunction"/> error.
    /// </summary>
    [LoggerMessage(
        EventId = 3,
        Level = LogLevel.Error,
        Message = "Function failed. Error: {Message}")]
    public static partial void LogFunctionError(
        this ILogger logger,
        Exception exception,
        string message);

    /// <summary>
    /// Logs <see cref="KernelFunction"/> complete.
    /// </summary>
    [LoggerMessage(
        EventId = 4,
        Level = LogLevel.Information,
        Message = "Function completed. Duration: {Duration}s")]
    public static partial void LogFunctionComplete(
        this ILogger logger,
        double duration);

    /// <summary>
    /// Logs streaming invocation of a <see cref="KernelFunction"/>.
    /// </summary>
    [LoggerMessage(
        EventId = 5,
        Level = LogLevel.Trace, // Sensitive data, logging as trace, disabled by default
        Message = "Function {FunctionName} streaming. Arguments: {Arguments}.")]
    public static partial void LogFunctionStreamingInvokingWithArguments(
        this ILogger logger,
        string functionName,
        KernelArguments arguments);

    /// <summary>
    /// Logs <see cref="KernelFunction"/> streaming complete.
    /// </summary>
    [LoggerMessage(
        EventId = 6,
        Level = LogLevel.Information,
        Message = "Function streaming completed. Duration: {Duration}s.")]
    public static partial void LogFunctionStreamingComplete(
        this ILogger logger,
        double duration);
}

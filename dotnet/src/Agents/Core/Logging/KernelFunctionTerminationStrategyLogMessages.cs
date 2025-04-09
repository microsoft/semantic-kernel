// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents.Chat;

#pragma warning disable SYSLIB1006 // Multiple logging methods cannot use the same event id within a class

/// <summary>
/// Extensions for logging <see cref="KernelFunctionTerminationStrategy"/> invocations.
/// </summary>
/// <remarks>
/// This extension uses the <see cref="LoggerMessageAttribute"/> to
/// generate logging code at compile time to achieve optimized code.
/// </remarks>
[ExcludeFromCodeCoverage]
[Experimental("SKEXP0110")]
internal static partial class KernelFunctionTerminationStrategyLogMessages
{
    /// <summary>
    /// Logs <see cref="KernelFunctionTerminationStrategy"/> invoking function (started).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Debug,
        Message = "[{MethodName}] Invoking function: {PluginName}.{FunctionName}.")]
    public static partial void LogKernelFunctionTerminationStrategyInvokingFunction(
        this ILogger logger,
        string methodName,
        string? pluginName,
        string functionName);

    /// <summary>
    /// Logs <see cref="KernelFunctionTerminationStrategy"/> invoked function (complete).
    /// </summary>
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "[{MethodName}] Invoked function: {PluginName}.{FunctionName}: {ResultType}")]
    public static partial void LogKernelFunctionTerminationStrategyInvokedFunction(
        this ILogger logger,
        string methodName,
        string? pluginName,
        string functionName,
        Type? resultType);
}

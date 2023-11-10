// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Reflection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

#pragma warning disable format

/// <summary>
/// Static helpers to create <seealso cref="ISKFunction"/> instances.
/// </summary>
public static class SKFunction
{
    /// <summary>
    /// Create a native function instance, wrapping a native object method
    /// </summary>
    /// <param name="method">Signature of the method to invoke</param>
    /// <param name="target">Object containing the method to invoke</param>
    /// <param name="pluginName">SK plugin name</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>SK function instance</returns>
    public static ISKFunction FromNativeMethod(
        MethodInfo method,
        object? target = null,
        string? pluginName = null,
        ILoggerFactory? loggerFactory = null)
            => NativeFunction.FromNativeMethod(method, target, pluginName, loggerFactory);

    /// <summary>
    /// Create a native function instance, wrapping a delegate function
    /// </summary>
    /// <param name="nativeFunction">Function to invoke</param>
    /// <param name="pluginName">SK plugin name</param>
    /// <param name="functionName">SK function name</param>
    /// <param name="description">SK function description</param>
    /// <param name="parameters">SK function parameters</param>
    /// <param name="returnParameter">SK function return parameter</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>SK function instance</returns>
    public static ISKFunction FromNativeFunction(
        Delegate nativeFunction,
        string? pluginName = null,
        string? functionName = null,
        string? description = null,
        IEnumerable<ParameterView>? parameters = null,
        ReturnParameterView? returnParameter = null,
        ILoggerFactory? loggerFactory = null)
            => NativeFunction.FromNativeFunction(nativeFunction, pluginName, functionName, description, parameters, returnParameter, loggerFactory);

    /// <summary>
    /// Default implementation to identify if a function was cancelled or skipped.
    /// </summary>
    /// <param name="context">Execution context</param>
    /// <returns>True if it was cancelled or skipped</returns>
    internal static bool IsInvokingCancelOrSkipRequested(SKContext context)
    {
        var eventArgs = context.FunctionInvokingHandler?.EventArgs;

        return IsInvokingCancelRequested(context) || IsInvokingSkipRequested(context);
    }

    /// <summary>
    /// Default implementation to identify if a function was skipped.
    /// </summary>
    /// <param name="context">Execution context</param>
    /// <returns>True if it was cancelled or skipped</returns>
    internal static bool IsInvokingSkipRequested(SKContext context)
    {
        return context.FunctionInvokingHandler?.EventArgs?.IsSkipRequested == true;
    }

    /// <summary>
    /// Default implementation to identify if a function was cancelled in the pre hook.
    /// </summary>
    /// <param name="context">Execution context</param>
    /// <returns>True if it was cancelled or skipped</returns>
    internal static bool IsInvokingCancelRequested(SKContext context)
    {
        return context.FunctionInvokingHandler?.EventArgs?.CancelToken.IsCancellationRequested == true;
    }

    /// <summary>
    /// Default implementation to identify if a function was cancelled in the post hook.
    /// </summary>
    /// <param name="context">Execution context</param>
    /// <returns>True if it was cancelled or skipped</returns>
    internal static bool IsInvokedCancelRequested(SKContext context)
    {
        return context.FunctionInvokedHandler?.EventArgs?.CancelToken.IsCancellationRequested == true;
    }
}

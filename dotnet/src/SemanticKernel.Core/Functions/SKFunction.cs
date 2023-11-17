// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Reflection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Models;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Factory methods for creating <seealso cref="ISKFunction"/> instances.
/// </summary>
public static class SKFunction
{
    /// <summary>
    /// Creates an <see cref="ISKFunction"/> instance for a method, specified via a delegate.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="ISKFunction"/>.</param>
    /// <param name="pluginName">The optional name of the plug-in associated with this method.</param>
    /// <param name="functionName">Optional function name. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">Optional description of the method. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="ISKFunction"/> wrapper for <paramref name="method"/>.</returns>
    public static ISKFunction Create(
        Delegate method,
        string? pluginName = null,
        string? functionName = null,
        string? description = null,
        IEnumerable<ParameterView>? parameters = null,
        ReturnParameterView? returnParameter = null,
        ILoggerFactory? loggerFactory = null) =>
        Create(method.Method, method.Target, pluginName, functionName, description, parameters, returnParameter, loggerFactory);

    /// <summary>
    /// Creates an <see cref="ISKFunction"/> instance for a method, specified via an <see cref="MethodInfo"/> instance
    /// and an optional target object if the method is an instance method.
    /// </summary>
    /// <param name="method">The method to be represented via the created <see cref="ISKFunction"/>.</param>
    /// <param name="target">The target object for the <paramref name="method"/> if it represents an instance method. This should be null if and only if <paramref name="method"/> is a static method.</param>
    /// <param name="pluginName">The optional name of the plug-in associated with this method.</param>
    /// <param name="functionName">Optional function name. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">Optional description of the method. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="ISKFunction"/> wrapper for <paramref name="method"/>.</returns>
    public static ISKFunction Create(
        MethodInfo method,
        object? target = null,
        string? pluginName = null,
        string? functionName = null,
        string? description = null,
        IEnumerable<ParameterView>? parameters = null,
        ReturnParameterView? returnParameter = null,
        ILoggerFactory? loggerFactory = null) =>
        NativeFunction.Create(method, target, pluginName, functionName, description, parameters, returnParameter, loggerFactory);

    /// <summary>
    /// Creates an <see cref="ISKFunction"/> instance for a semantic function using the specified <see cref="PromptFunctionModel"/>.
    /// </summary>
    /// <param name="promptFunctionModel">Instance of <see cref="PromptFunctionModel"/> to use to create the semantic function</param>
    /// <param name="pluginName">The optional name of the plug-in associated with this method.</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="ISKFunction"/> wrapper for <paramref name="promptFunctionModel"/>.</returns>
    public static ISKFunction Create(
        PromptFunctionModel promptFunctionModel,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null) =>
        SemanticFunction.Create(promptFunctionModel, pluginName, promptTemplateFactory, loggerFactory);

    #region Obsolete
    /// <summary>
    /// Create a native function instance, wrapping a native object method
    /// </summary>
    /// <param name="method">Signature of the method to invoke</param>
    /// <param name="target">Object containing the method to invoke</param>
    /// <param name="pluginName">SK plugin name</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>SK function instance</returns>
    [EditorBrowsable(EditorBrowsableState.Never)]
    [Obsolete("This method will be removed in a future release. Use SKFunction.Create instead.")]
    public static ISKFunction FromNativeMethod(
        MethodInfo method,
        object? target = null,
        string? pluginName = null,
        ILoggerFactory? loggerFactory = null) =>
        Create(method, target, pluginName, loggerFactory: loggerFactory);

    /// <summary>
    /// Create a native function instance, wrapping a delegate function
    /// </summary>
    /// <param name="nativeFunction">Function to invoke</param>
    /// <param name="pluginName">SK plugin name</param>
    /// <param name="functionName">SK function name</param>
    /// <param name="description">SK function description</param>
    /// <param name="parameters">SK function parameters</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>SK function instance</returns>
    [EditorBrowsable(EditorBrowsableState.Never)]
    [Obsolete("This method will be removed in a future release. Use SKFunction.Create instead.")]
    public static ISKFunction FromNativeFunction(
        Delegate nativeFunction,
        string? pluginName = null,
        string? functionName = null,
        string? description = null,
        IEnumerable<ParameterView>? parameters = null,
        ILoggerFactory? loggerFactory = null) =>
        Create(nativeFunction, pluginName, functionName, description, parameters, null, loggerFactory);
    #endregion

    #region Internal
    /// <summary>
    /// Default implementation to identify if a function was cancelled or skipped.
    /// </summary>
    /// <param name="context">Execution context</param>
    /// <returns>True if it was cancelled or skipped</returns>
    internal static bool IsInvokingCancelOrSkipRequested(SKContext context) =>
        IsInvokingCancelRequested(context) || IsInvokingSkipRequested(context);

    /// <summary>
    /// Default implementation to identify if a function was skipped.
    /// </summary>
    /// <param name="context">Execution context</param>
    /// <returns>True if it was cancelled or skipped</returns>
    internal static bool IsInvokingSkipRequested(SKContext context) =>
        context.FunctionInvokingHandler?.EventArgs?.IsSkipRequested == true;

    /// <summary>
    /// Default implementation to identify if a function was cancelled in the pre hook.
    /// </summary>
    /// <param name="context">Execution context</param>
    /// <returns>True if it was cancelled or skipped</returns>
    internal static bool IsInvokingCancelRequested(SKContext context) =>
        context.FunctionInvokingHandler?.EventArgs?.CancelToken.IsCancellationRequested == true;

    /// <summary>
    /// Default implementation to identify if a function was cancelled in the post hook.
    /// </summary>
    /// <param name="context">Execution context</param>
    /// <returns>True if it was cancelled or skipped</returns>
    internal static bool IsInvokedCancelRequested(SKContext context) =>
        context.FunctionInvokedHandler?.EventArgs?.CancelToken.IsCancellationRequested == true;
    #endregion
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Reflection;
using Microsoft.Extensions.Logging;

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
    /// Create a method-level function instance, wrapping a object method
    /// </summary>
    /// <param name="method">Signature of the method to invoke</param>
    /// <param name="target">Object containing the method to invoke</param>
    /// <param name="pluginName">SK plugin name</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>SK function instance</returns>
    public static ISKFunction FromMethod(
        MethodInfo method,
        object? target = null,
        string? pluginName = null,
        ILoggerFactory? loggerFactory = null)
            => MethodLevelFunction.FromMethod(method, target, pluginName, loggerFactory);

    /// <summary>
    /// Create a method-level function instance, wrapping a delegate function
    /// </summary>
    /// <param name="delegatedFunction">Function to invoke</param>
    /// <param name="pluginName">SK plugin name</param>
    /// <param name="functionName">SK function name</param>
    /// <param name="description">SK function description</param>
    /// <param name="parameters">SK function parameters</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>SK function instance</returns>
    public static ISKFunction FromMethod(
        Delegate delegatedFunction,
        string? pluginName = null,
        string? functionName = null,
        string? description = null,
        IEnumerable<ParameterView>? parameters = null,
        ILoggerFactory? loggerFactory = null)
            => MethodLevelFunction.FromMethod(delegatedFunction, pluginName, functionName, description, parameters, loggerFactory);
}

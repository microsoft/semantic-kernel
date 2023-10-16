// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel;

/// <summary>Extension methods for interacting with <see cref="IKernel"/>.</summary>
public static class KernelExtensions
{
    /// <summary>
    /// Import a set of functions as a plugin from the given object instance. Only the functions that have the `SKFunction` attribute will be included in the plugin.
    /// Once these functions are imported, the prompt templates can use functions to import content at runtime.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="functionsInstance">Instance of a class containing functions</param>
    /// <param name="pluginName">Name of the plugin for function collection and prompt templates. If the value is empty functions are registered in the global namespace.</param>
    /// <returns>A list of all the semantic functions found in the directory, indexed by function name.</returns>
    public static IDictionary<string, ISKFunction> ImportFunctions(
        this IKernel kernel,
        object functionsInstance,
        string? pluginName = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(functionsInstance);

        ILogger logger = kernel.LoggerFactory.CreateLogger(kernel.GetType());
        if (string.IsNullOrWhiteSpace(pluginName))
        {
            pluginName = FunctionCollection.GlobalFunctionsPluginName;
            logger.LogTrace("Importing functions from {0} to the global plugin namespace", functionsInstance.GetType().FullName);
        }
        else
        {
            logger.LogTrace("Importing functions from {0} to the {1} namespace", functionsInstance.GetType().FullName, pluginName);
        }

        MethodInfo[] methods = functionsInstance.GetType().GetMethods(BindingFlags.Static | BindingFlags.Instance | BindingFlags.Public);
        logger.LogTrace("Importing plugin name: {0}. Potential methods found: {1}", pluginName, methods.Length);

        // Filter out non-SKFunctions and fail if two functions have the same name
        Dictionary<string, ISKFunction> result = new(StringComparer.OrdinalIgnoreCase);
        foreach (MethodInfo method in methods)
        {
            if (method.GetCustomAttribute<SKFunctionAttribute>() is not null)
            {
                ISKFunction function = SKFunction.FromNativeMethod(method, functionsInstance, pluginName, kernel.LoggerFactory);
                if (result.ContainsKey(function.Name))
                {
                    throw new SKException("Function overloads are not supported, please differentiate function names");
                }

                result.Add(function.Name, function);
            }
        }

        logger.LogTrace("Methods imported {0}", result.Count);

        foreach (KeyValuePair<string, ISKFunction> f in result)
        {
            kernel.RegisterCustomFunction(f.Value);
        }

        return result;
    }

    /// <summary>
    /// Run a single synchronous or asynchronous <see cref="ISKFunction"/>.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="skFunction">A Semantic Kernel function to run</param>
    /// <param name="variables">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the function</returns>
    public static Task<KernelResult> RunAsync(
        this IKernel kernel,
        ISKFunction skFunction,
        ContextVariables? variables = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        return kernel.RunAsync(variables ?? new(), cancellationToken, skFunction);
    }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    public static Task<KernelResult> RunAsync(
        this IKernel kernel,
        params ISKFunction[] pipeline)
    {
        Verify.NotNull(kernel);
        return kernel.RunAsync(new ContextVariables(), pipeline);
    }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="input">Input to process</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    public static Task<KernelResult> RunAsync(
        this IKernel kernel,
        string input,
        params ISKFunction[] pipeline)
    {
        Verify.NotNull(kernel);
        return kernel.RunAsync(new ContextVariables(input), pipeline);
    }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="variables">Input to process</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    public static Task<KernelResult> RunAsync(
        this IKernel kernel,
        ContextVariables variables,
        params ISKFunction[] pipeline)
    {
        Verify.NotNull(kernel);
        return kernel.RunAsync(variables, CancellationToken.None, pipeline);
    }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    public static Task<KernelResult> RunAsync(
        this IKernel kernel,
        CancellationToken cancellationToken,
        params ISKFunction[] pipeline)
    {
        Verify.NotNull(kernel);
        return kernel.RunAsync(new ContextVariables(), cancellationToken, pipeline);
    }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="input">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    public static Task<KernelResult> RunAsync(
        this IKernel kernel,
        string input,
        CancellationToken cancellationToken,
        params ISKFunction[] pipeline)
    {
        Verify.NotNull(kernel);
        return kernel.RunAsync(new ContextVariables(input), cancellationToken, pipeline);
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel;

/// <summary>Extension methods for interacting with <see cref="Kernel"/>.</summary>
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
        this Kernel kernel,
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
                ISKFunction function = SKFunction.Create(method, functionsInstance, pluginName, loggerFactory: kernel.LoggerFactory);
                if (result.ContainsKey(function.Name))
                {
                    throw new SKException("Function overloads are not supported. Differentiate function names.");
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
        this Kernel kernel,
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
        this Kernel kernel,
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
        this Kernel kernel,
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
        this Kernel kernel,
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
        this Kernel kernel,
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
        this Kernel kernel,
        string input,
        CancellationToken cancellationToken,
        params ISKFunction[] pipeline)
    {
        Verify.NotNull(kernel);
        return kernel.RunAsync(new ContextVariables(input), cancellationToken, pipeline);
    }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="variables">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    /// <inheritdoc/>
    public static async Task<KernelResult> RunAsync(this Kernel kernel, ContextVariables variables, CancellationToken cancellationToken, params ISKFunction[] pipeline)
    {
        var context = kernel.CreateNewContext(variables);

        FunctionResult? functionResult = null;

        int pipelineStepCount = 0;
        var allFunctionResults = new List<FunctionResult>();

        var logger = kernel.LoggerFactory.CreateLogger(typeof(Kernel));

        foreach (ISKFunction skFunction in pipeline)
        {
repeat:
            cancellationToken.ThrowIfCancellationRequested();

            try
            {
                var functionDetails = skFunction.Describe();

                functionResult = await skFunction.InvokeAsync(context, null, cancellationToken: cancellationToken).ConfigureAwait(false);

                if (IsCancelRequested(skFunction, functionResult.Context, pipelineStepCount, logger))
                {
                    break;
                }

                if (IsSkipRequested(skFunction, functionResult.Context, pipelineStepCount, logger))
                {
                    continue;
                }

                // Only non-stop results are considered as Kernel results
                allFunctionResults.Add(functionResult!);

                if (IsRepeatRequested(skFunction, functionResult.Context, pipelineStepCount, logger))
                {
                    goto repeat;
                }
            }
            catch (Exception ex)
            {
                logger.LogError("Plugin {Plugin} function {Function} call fail during pipeline step {Step} with error {Error}:", skFunction.PluginName, skFunction.Name, pipelineStepCount, ex.Message);
                throw;
            }

            pipelineStepCount++;
        }

        return KernelResult.FromFunctionResults(allFunctionResults.LastOrDefault()?.Value, allFunctionResults);
    }

    /// <summary>
    /// Checks if the handler requested to cancel the function execution.
    /// </summary>
    /// <param name="skFunction">Target function</param>
    /// <param name="context">Context of execution</param>
    /// <param name="pipelineStepCount">Current pipeline step</param>
    /// <param name="logger">The logger.</param>
    /// <returns></returns>
    private static bool IsCancelRequested(ISKFunction skFunction, SKContext context, int pipelineStepCount, ILogger logger)
    {
        if (SKFunction.IsInvokingCancelRequested(context))
        {
            logger.LogInformation("Execution was cancelled on function invoking event of pipeline step {StepCount}: {PluginName}.{FunctionName}.", pipelineStepCount, skFunction.PluginName, skFunction.Name);
            return true;
        }

        if (SKFunction.IsInvokedCancelRequested(context))
        {
            logger.LogInformation("Execution was cancelled on function invoked event of pipeline step {StepCount}: {PluginName}.{FunctionName}.", pipelineStepCount, skFunction.PluginName, skFunction.Name);
            return true;
        }

        return false;
    }

    /// <summary>
    /// Checks if the handler requested to skip the function execution.
    /// </summary>
    /// <param name="skFunction">Target function</param>
    /// <param name="context">Context of execution</param>
    /// <param name="pipelineStepCount">Current pipeline step</param>
    /// <param name="logger">The logger.</param>
    /// <returns></returns>
    private static bool IsSkipRequested(ISKFunction skFunction, SKContext context, int pipelineStepCount, ILogger logger)
    {
        if (SKFunction.IsInvokingSkipRequested(context))
        {
            logger.LogInformation("Execution was skipped on function invoking event of pipeline step {StepCount}: {PluginName}.{FunctionName}.", pipelineStepCount, skFunction.PluginName, skFunction.Name);
            return true;
        }

        return false;
    }

    /// <summary>
    /// Checks if the handler requested to repeat the function execution.
    /// </summary>
    /// <param name="skFunction">Target function</param>
    /// <param name="context">Context of execution</param>
    /// <param name="pipelineStepCount">Current pipeline step</param>
    /// <param name="logger">The logger.</param>
    /// <returns></returns>
    private static bool IsRepeatRequested(ISKFunction skFunction, SKContext context, int pipelineStepCount, ILogger logger)
    {
        if (context.FunctionInvokedHandler?.EventArgs?.IsRepeatRequested ?? false)
        {
            logger.LogInformation("Execution repeat request on function invoked event of pipeline step {StepCount}: {PluginName}.{FunctionName}.", pipelineStepCount, skFunction.PluginName, skFunction.Name);
            return true;
        }
        return false;
    }
}

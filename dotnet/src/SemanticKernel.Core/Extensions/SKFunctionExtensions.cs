// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130 // Namespace does not match folder structure

/// <summary>
/// Class that holds extension methods for objects implementing KernelFunction.
/// </summary>
public static class SKFunctionExtensions
{
    /// <summary>
    /// Execute a function allowing to pass the main input separately from the rest of the context.
    /// </summary>
    /// <param name="function">Function to execute</param>
    /// <param name="kernel">Kernel</param>
    /// <param name="variables">Input variables for the function</param>
    /// <param name="plugins">Collection of plugins that this function can access</param>
    /// <param name="requestSettings">LLM completion settings (for semantic functions only)</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function execution</returns>
    public static Task<FunctionResult> InvokeAsync(this KernelFunction function,
        Kernel kernel,
        ContextVariables? variables = null,
        IReadOnlySKPluginCollection? plugins = null,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        var context = kernel.CreateNewContext(variables, plugins);
        return function.InvokeAsync(kernel, context, requestSettings, cancellationToken);
    }

    /// <summary>
    /// Execute a function allowing to pass the main input separately from the rest of the context.
    /// </summary>
    /// <param name="function">Function to execute</param>
    /// <param name="kernel">Kernel</param>
    /// <param name="input">Input string for the function</param>
    /// <param name="plugins">Collection of plugins that this function can access</param>
    /// <param name="requestSettings">LLM completion settings (for semantic functions only)</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function execution</returns>
    public static Task<FunctionResult> InvokeAsync(this KernelFunction function,
        Kernel kernel,
        string input,
        IReadOnlySKPluginCollection? plugins = null,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
        => function.InvokeAsync(kernel, new ContextVariables(input), plugins, requestSettings, cancellationToken);
}

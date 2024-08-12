// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' functions to the LLM to call or specific ones.
/// This behavior allows the LLM to decide whether to call the functions and, if so, which ones to call.
/// </summary>
internal sealed class AutoFunctionChoiceBehavior : FunctionChoiceBehavior
{
    /// <summary>
    /// List of the functions to provide to LLM.
    /// </summary>
    private readonly IEnumerable<KernelFunction>? _functions;

    /// <summary>
    /// Indicates whether the functions should be automatically invoked by AI connectors.
    /// </summary>
    private readonly bool _autoInvoke;

    /// <summary>
    /// Initializes a new instance of the <see cref="AutoFunctionChoiceBehavior"/> class.
    /// </summary>
    /// <param name="functions">
    /// Functions to provide to LLM. If null, all <see cref="Kernel"/>'s plugins' functions are provided to LLM.
    /// If empty, no functions are provided to LLM, which is equivalent to disabling function calling.
    /// </param>
    /// <param name="autoInvoke">
    /// Indicates whether the functions should be automatically invoked by AI connectors.
    /// </param>
    public AutoFunctionChoiceBehavior(IEnumerable<KernelFunction>? functions = null, bool autoInvoke = true)
    {
        this._functions = functions;
        this._autoInvoke = autoInvoke;
    }

    /// <inheritdoc />
#pragma warning disable SKEXP0010 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorConfigurationContext context)
#pragma warning restore SKEXP0010 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
    {
        // If auto-invocation is specified, we need a kernel to be able to invoke the functions.
        // Lack of a kernel is fatal: we don't want to tell the model we can handle the functions
        // and then fail to do so, so we fail before we get to that point. This is an error
        // on the consumers behalf: if they specify auto-invocation with any functions, they must
        // specify the kernel and the kernel must contain those functions.
        if (this._autoInvoke && context.Kernel is null)
        {
            throw new KernelException("Auto-invocation is not supported when no kernel is provided.");
        }

        List<KernelFunction>? availableFunctions = null;
        bool allowAnyRequestedKernelFunction = false;

        if (this._functions is not null)
        {
            availableFunctions = new List<KernelFunction>(this._functions.Count());

            foreach (var function in this._functions)
            {
                if (this._autoInvoke)
                {
                    // If auto-invocation is requested and no function is found in the kernel, fail early.
                    if (!context.Kernel!.Plugins.TryGetFunction(function.PluginName, function.Name, out var _))
                    {
                        throw new KernelException($"The specified function {function} is not available in the kernel.");
                    }
                }

                availableFunctions.Add(function);
            }
        }
        // Provide all kernel functions.
        else if (context.Kernel is not null)
        {
            allowAnyRequestedKernelFunction = true;

            foreach (var plugin in context.Kernel.Plugins)
            {
                (availableFunctions ??= new List<KernelFunction>(context.Kernel.Plugins.Count)).AddRange(plugin);
            }
        }

#pragma warning disable SKEXP0010 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        return new FunctionChoiceBehaviorConfiguration()
        {
            Choice = FunctionChoice.Auto,
            Functions = availableFunctions,
            AutoInvoke = this._autoInvoke,
            AllowAnyRequestedKernelFunction = allowAnyRequestedKernelFunction
        };
#pragma warning restore SKEXP0010 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
    }
}

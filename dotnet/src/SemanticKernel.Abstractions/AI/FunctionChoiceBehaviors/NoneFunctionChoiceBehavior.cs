// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' functions to the AI model to call or specific ones.
/// This behavior instructs the model not to call any functions and only to generate a user-facing message.
/// </summary>
/// <remarks>
/// Although this behavior prevents the model from calling any functions, the model can use the provided function information
/// to describe how it would complete the prompt if it had the ability to call the functions.
/// </remarks>
internal sealed class NoneFunctionChoiceBehavior : FunctionChoiceBehavior
{
    /// <summary>
    /// List of the functions to provide to AI model.
    /// </summary>
    private readonly IEnumerable<KernelFunction>? _functions;

    /// <summary>
    /// Initializes a new instance of the <see cref="NoneFunctionChoiceBehavior"/> class.
    /// </summary>
    /// <param name="functions">
    /// Functions to provide to AI model. If null, all <see cref="Kernel"/>'s plugins' functions are provided to the model.
    /// If empty, no functions are provided to the model, which is equivalent to disabling function calling.
    /// </param>
    public NoneFunctionChoiceBehavior(IEnumerable<KernelFunction>? functions = null)
    {
        this._functions = functions;
    }

    /// <inheritdoc/>
    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorConfigurationContext context)
    {
        List<KernelFunction>? availableFunctions = null;

        if (this._functions is not null)
        {
            availableFunctions = new List<KernelFunction>(this._functions);
        }
        // Provide all kernel functions.
        else if (context.Kernel is not null)
        {
            foreach (var plugin in context.Kernel.Plugins)
            {
                (availableFunctions ??= new List<KernelFunction>(context.Kernel.Plugins.Count)).AddRange(plugin);
            }
        }

#pragma warning disable SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
        return new FunctionChoiceBehaviorConfiguration()
        {
            Choice = FunctionChoice.None,
            Functions = availableFunctions,
            AutoInvoke = false,
        };
#pragma warning restore SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
    }
}

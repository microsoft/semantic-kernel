﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' functions to AI model to call or specific ones but instructs it not to call any of them.
/// The model may use the provided function in the response it generates. E.g. the model may describe which functions it would call and with what parameter values.
/// This response is useful if the user should first validate what functions the model will use.
/// </summary>
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
    /// If empty, no functions are provided to the model.
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
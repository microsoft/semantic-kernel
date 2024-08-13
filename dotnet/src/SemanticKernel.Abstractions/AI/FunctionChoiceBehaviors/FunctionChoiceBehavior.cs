// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the base class for different function choice behaviors.
/// These behaviors define the way functions are chosen by LLM and various aspects of their invocation by AI connectors.
/// </summary>
[Experimental("SKEXP0001")]
public abstract class FunctionChoiceBehavior
{
    /// <summary>
    /// Gets an instance of the <see cref="FunctionChoiceBehavior"/> that provides either all of the<see cref="Kernel"/>'s plugins' functions to the LLM to call or specific ones.
    /// This behavior allows the LLM to decide whether to call the functions and, if so, which ones to call.
    /// </summary>
    /// <param name="functions">
    /// Functions to provide to LLM. If null, all <see cref="Kernel"/>'s plugins' functions are provided to LLM.
    /// If empty, no functions are provided to LLM, which is equivalent to disabling function calling.
    /// </param>
    /// <param name="autoInvoke">
    /// Indicates whether the functions should be automatically invoked by AI connectors.
    /// </param>
    [Experimental("SKEXP0001")]
    public static FunctionChoiceBehavior Auto(IEnumerable<KernelFunction>? functions = null, bool autoInvoke = true)
    {
        return new AutoFunctionChoiceBehavior(functions, autoInvoke);
    }

    /// <summary>
    /// Returns the configuration used by AI connectors to determine function choice and invocation behavior.
    /// </summary>
    /// <param name="context">The context provided by AI connectors, used to determine the configuration.</param>
    /// <returns>The configuration.</returns>
#pragma warning disable SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
    public abstract FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorConfigurationContext context);
#pragma warning restore SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
}

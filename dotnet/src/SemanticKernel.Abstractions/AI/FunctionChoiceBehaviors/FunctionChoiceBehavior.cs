// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the base class for different function choice behaviors.
/// These behaviors define the way functions are chosen by AI model and various aspects of their invocation by AI connectors.
/// </summary>
[Experimental("SKEXP0001")]
[JsonPolymorphic(TypeDiscriminatorPropertyName = "type")]
[JsonDerivedType(typeof(AutoFunctionChoiceBehavior), typeDiscriminator: "auto")]
[JsonDerivedType(typeof(RequiredFunctionChoiceBehavior), typeDiscriminator: "required")]
[JsonDerivedType(typeof(NoneFunctionChoiceBehavior), typeDiscriminator: "none")]
public abstract class FunctionChoiceBehavior
{
    /// <summary>The separator used to separate plugin name and function name.</summary>
    protected const string FunctionNameSeparator = ".";

    /// <summary>The behavior default options.</summary>
    protected static readonly FunctionChoiceBehaviorOptions DefaultOptions = new();

    /// <summary>
    /// List of the functions to provide to AI model.
    /// </summary>
    private readonly IEnumerable<KernelFunction>? _functions;

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionChoiceBehavior"/> class.
    /// </summary>
    internal FunctionChoiceBehavior()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionChoiceBehavior"/> class.
    /// </summary>
    /// <param name="functions">
    /// Functions to provide to AI model. If null, all <see cref="Kernel"/>'s plugins' functions are provided to the model.
    /// If empty, no functions are provided to the model.
    /// </param>
    internal FunctionChoiceBehavior(IEnumerable<KernelFunction>? functions = null)
    {
        this._functions = functions;
    }

    /// <summary>
    /// Gets an instance of the <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' functions to the AI model to call or specific ones.
    /// This behavior allows the model to decide whether to call the functions and, if so, which ones to call.
    /// </summary>
    /// <param name="functions">
    /// Functions to provide to the model. If null, all of the <see cref="Kernel"/>'s plugins' functions are provided to the model.
    /// If empty, no functions are provided to the model, which is equivalent to disabling function calling.
    /// </param>
    /// <param name="autoInvoke">
    /// Indicates whether the functions should be automatically invoked by AI connectors.
    /// </param>
    /// <param name="options">The behavior options.</param>
    /// <returns>An instance of one of the <see cref="FunctionChoiceBehavior"/>.</returns>
    public static FunctionChoiceBehavior Auto(IEnumerable<KernelFunction>? functions = null, bool autoInvoke = true, FunctionChoiceBehaviorOptions? options = null)
    {
        return new AutoFunctionChoiceBehavior(functions, autoInvoke, options);
    }

    /// <summary>
    /// Gets an instance of the <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' functions to the AI model to call or specific ones.
    /// This behavior forces the model to always call one or more functions.
    /// </summary>
    /// <param name="functions">
    /// Functions to provide to the model. If null, all of the <see cref="Kernel"/>'s plugins' functions are provided to the model.
    /// If empty, no functions are provided to the model, which is equivalent to disabling function calling.
    /// </param>
    /// <param name="autoInvoke">
    /// Indicates whether the functions should be automatically invoked by AI connectors.
    /// </param>
    /// <param name="functionsSelector">
    /// The callback function allows customization of function selection.
    /// It accepts functions, chat history, and an optional kernel, and returns a list of functions to be used by the AI model.
    /// This should be supplied to prevent the AI model from repeatedly calling functions even when the prompt has already been answered.
    /// For example, if the AI model is prompted to calculate the sum of two numbers, 2 and 3, and is provided with the 'Add' function,
    /// the model will keep calling the 'Add' function even if the sum - 5 - is already calculated, until the 'Add' function is no longer provided to the model.
    /// In this example, the function selector can analyze chat history and decide not to advertise the 'Add' function anymore.
    /// </param>
    /// <param name="options">The behavior options.</param>
    /// <returns>An instance of one of the <see cref="FunctionChoiceBehavior"/>.</returns>
    public static FunctionChoiceBehavior Required(
        IEnumerable<KernelFunction>? functions = null,
        bool autoInvoke = true, Func<FunctionChoiceBehaviorFunctionsSelectorContext, IReadOnlyList<KernelFunction>?>? functionsSelector = null,
        FunctionChoiceBehaviorOptions? options = null)
    {
        return new RequiredFunctionChoiceBehavior(functions, autoInvoke, functionsSelector, options);
    }

    /// <summary>
    /// Gets an instance of the <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' functions to AI model to call or specific ones but instructs it not to call any of them.
    /// The model may use the provided function in the response it generates. E.g. the model may describe which functions it would call and with what parameter values.
    /// This response is useful if the user should first validate what functions the model will use.
    /// </summary>
    /// <param name="functions">
    /// Functions to provide to the model. If null, all of the <see cref="Kernel"/>'s plugins' functions are provided to the model.
    /// If empty, no functions are provided to the model.
    /// </param>
    /// <param name="options">The behavior options.</param>
    /// <returns>An instance of one of the <see cref="FunctionChoiceBehavior"/>.</returns>
    public static FunctionChoiceBehavior None(IEnumerable<KernelFunction>? functions = null, FunctionChoiceBehaviorOptions? options = null)
    {
        return new NoneFunctionChoiceBehavior(functions, options);
    }

    /// <summary>
    /// Returns the configuration used by AI connectors to determine function choice and invocation behavior.
    /// </summary>
    /// <param name="context">The context provided by AI connectors, used to determine the configuration.</param>
    /// <returns>The configuration.</returns>
#pragma warning disable SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
    public abstract FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorConfigurationContext context);

    /// <summary>
    /// Returns functions AI connector should provide to the AI model.
    /// </summary>
    /// <param name="functionFQNs">Functions provided as fully qualified names.</param>
    /// <param name="kernel">The <see cref="Kernel"/> to be used for function calling.</param>
    /// <param name="autoInvoke">Indicates whether the functions should be automatically invoked by the AI connector.</param>
    /// <returns>The configuration.</returns>
    protected IReadOnlyList<KernelFunction>? GetFunctions(IList<string>? functionFQNs, Kernel? kernel, bool autoInvoke)
    {
        // If auto-invocation is specified, we need a kernel to be able to invoke the functions.
        // Lack of a kernel is fatal: we don't want to tell the model we can handle the functions
        // and then fail to do so, so we fail before we get to that point. This is an error
        // on the consumers behalf: if they specify auto-invocation with any functions, they must
        // specify the kernel and the kernel must contain those functions.
        if (autoInvoke && kernel is null)
        {
            throw new KernelException("Auto-invocation is not supported when no kernel is provided.");
        }

        List<KernelFunction>? availableFunctions = null;

        if (functionFQNs is { Count: > 0 })
        {
            availableFunctions = new List<KernelFunction>(functionFQNs.Count);

            foreach (var functionFQN in functionFQNs)
            {
                var nameParts = FunctionName.Parse(functionFQN, FunctionNameSeparator);

                // Look up the function in the kernel.
                if (kernel is not null && kernel.Plugins.TryGetFunction(nameParts.PluginName, nameParts.Name, out var function))
                {
                    availableFunctions.Add(function);
                    continue;
                }

                // If auto-invocation is requested and no function is found in the kernel, fail early.
                if (autoInvoke)
                {
                    throw new KernelException($"The specified function {functionFQN} is not available in the kernel.");
                }

                // Look up the function in the list of functions provided as instances of KernelFunction.
                function = this._functions?.FirstOrDefault(f => f.Name == nameParts.Name && f.PluginName == nameParts.PluginName);
                if (function is not null)
                {
                    availableFunctions.Add(function);
                    continue;
                }

                throw new KernelException($"The specified function {functionFQN} was not found.");
            }
        }
        // Disable function calling.
        else if (functionFQNs is { Count: 0 })
        {
            return availableFunctions;
        }
        // Provide all kernel functions.
        else if (kernel is not null)
        {
            foreach (var plugin in kernel.Plugins)
            {
                (availableFunctions ??= new List<KernelFunction>(kernel.Plugins.Count)).AddRange(plugin);
            }
        }

        return availableFunctions;
    }
}

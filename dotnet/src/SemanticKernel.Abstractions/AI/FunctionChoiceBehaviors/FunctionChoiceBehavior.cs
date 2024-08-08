// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the base class for different function choice behaviors.
/// </summary>
[JsonPolymorphic(TypeDiscriminatorPropertyName = "type")]
[JsonDerivedType(typeof(AutoFunctionChoiceBehavior), typeDiscriminator: "auto")]
[JsonDerivedType(typeof(RequiredFunctionChoiceBehavior), typeDiscriminator: "required")]
[JsonDerivedType(typeof(NoneFunctionChoiceBehavior), typeDiscriminator: "none")]
public abstract class FunctionChoiceBehavior
{
    /// <summary>The separator used to separate plugin name and function name.</summary>
    protected const string FunctionNameSeparator = ".";

    /// <summary>
    /// Creates a new instance of the <see cref="FunctionChoiceBehavior"/> class.
    /// </summary>
    internal FunctionChoiceBehavior()
    {
    }

    /// <summary>
    /// Gets an instance of the <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' function information to the model or a specified subset.
    /// This behavior allows the model to decide whether to call the functions and, if so, which ones to call.
    /// </summary>
    /// <param name="functions">The subset of the <see cref="Kernel"/>'s plugins' functions to provide to the model.
    /// If null or empty, all <see cref="Kernel"/>'s plugins' functions are provided to the model.</param>
    /// <param name="autoInvoke">Indicates whether the functions should be automatically invoked by the AI service/connector.</param>
    /// <returns>An instance of one of the <see cref="FunctionChoiceBehavior"/>.</returns>
    public static FunctionChoiceBehavior Auto(IEnumerable<KernelFunction>? functions, bool autoInvoke)
    {
        return new AutoFunctionChoiceBehavior(functions, new FunctionChoiceBehaviorOptions() { AutoInvoke = autoInvoke });
    }

    /// <summary>
    /// Gets an instance of the <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' function information to the model or a specified subset.
    /// This behavior allows the model to decide whether to call the functions and, if so, which ones to call.
    /// </summary>
    /// <param name="functions">The subset of the <see cref="Kernel"/>'s plugins' functions to provide to the model.
    /// If null or empty, all <see cref="Kernel"/>'s plugins' functions are provided to the model.</param>
    /// <param name="options">The options for the behavior.</param>
    /// <returns>An instance of one of the <see cref="FunctionChoiceBehavior"/>.</returns>
    public static FunctionChoiceBehavior Auto(IEnumerable<KernelFunction>? functions = null, FunctionChoiceBehaviorOptions? options = null)
    {
        return new AutoFunctionChoiceBehavior(functions, options);
    }

    /// <summary>
    /// Gets an instance of the <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' function information to the model or a specified subset.
    /// This behavior forces the model to always call one or more functions. The model will then select which function(s) to call.
    /// </summary>
    /// <param name="functions">The subset of the <see cref="Kernel"/>'s plugins' functions to provide to the model.
    /// If null or empty, all <see cref="Kernel"/>'s plugins' functions are provided to the model.</param>
    /// <param name="autoInvoke">Indicates whether the functions should be automatically invoked by the AI service/connector.</param>
    /// <returns>An instance of one of the <see cref="FunctionChoiceBehavior"/>.</returns>
    public static FunctionChoiceBehavior Required(IEnumerable<KernelFunction>? functions, bool autoInvoke)
    {
        return new RequiredFunctionChoiceBehavior(functions, new FunctionChoiceBehaviorOptions { AutoInvoke = autoInvoke });
    }

    /// <summary>
    /// Gets an instance of the <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' function information to the model or a specified subset.
    /// This behavior forces the model to always call one or more functions. The model will then select which function(s) to call.
    /// </summary>
    /// <param name="functions">The subset of the <see cref="Kernel"/>'s plugins' functions to provide to the model.
    /// If null or empty, all <see cref="Kernel"/>'s plugins' functions are provided to the model.</param>
    /// <param name="options">The options for the behavior.</param>
    /// <returns>An instance of one of the <see cref="FunctionChoiceBehavior"/>.</returns>
    public static FunctionChoiceBehavior Required(IEnumerable<KernelFunction>? functions = null, FunctionChoiceBehaviorOptions? options = null)
    {
        return new RequiredFunctionChoiceBehavior(functions, options);
    }

    /// <summary>
    /// Gets an instance of the <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' function information to the model or a specified subset.
    /// This behavior forces the model to not call any functions and only generate a user-facing message.
    /// </summary>
    /// <param name="functions">The subset of the <see cref="Kernel"/>'s plugins' functions to provide to the model.
    /// If null or empty, all <see cref="Kernel"/>'s plugins' functions are provided to the model.</param>
    /// <param name="autoInvoke">Indicates whether the functions should be automatically invoked by the AI service/connector.</param>
    /// <returns>An instance of one of the <see cref="FunctionChoiceBehavior"/>.</returns>
    /// <remarks>
    /// Although this behavior prevents the model from calling any functions, the model can use the provided function information
    /// to describe how it would complete the prompt if it had the ability to call the functions.
    /// </remarks>
    public static FunctionChoiceBehavior None(IEnumerable<KernelFunction>? functions, bool autoInvoke)
    {
        return new NoneFunctionChoiceBehavior(functions, new FunctionChoiceBehaviorOptions { AutoInvoke = autoInvoke });
    }

    /// <summary>
    /// Gets an instance of the <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' function information to the model or a specified subset.
    /// This behavior forces the model to not call any functions and only generate a user-facing message.
    /// </summary>
    /// <param name="functions">The subset of the <see cref="Kernel"/>'s plugins' functions to provide to the model.
    /// If null or empty, all <see cref="Kernel"/>'s plugins' functions are provided to the model.</param>
    /// <param name="options">The options for the behavior.</param>
    /// <returns>An instance of one of the <see cref="FunctionChoiceBehavior"/>.</returns>
    /// <remarks>
    /// Although this behavior prevents the model from calling any functions, the model can use the provided function information
    /// to describe how it would complete the prompt if it had the ability to call the functions.
    /// </remarks>
    public static FunctionChoiceBehavior None(IEnumerable<KernelFunction>? functions = null, FunctionChoiceBehaviorOptions? options = null)
    {
        return new NoneFunctionChoiceBehavior(functions, options);
    }

    /// <summary>Returns the configuration specified by the <see cref="FunctionChoiceBehavior"/>.</summary>
    /// <param name="context">The function choice caller context.</param>
    /// <returns>The configuration.</returns>
    public abstract FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorContext context);

    /// <summary>
    /// Returns the functions that the model can choose from.
    /// </summary>
    /// <param name="functionFQNs">Functions provided as fully qualified names.</param>
    /// <param name="functions">Functions provided as instances of <see cref="KernelFunction"/>.</param>
    /// <param name="kernel">/// The <see cref="Kernel"/> to be used for function calling.</param>
    /// <param name="autoInvoke">Indicates whether the functions should be automatically invoked by the AI service/connector.</param>
    /// <returns>The functions that the model can choose from and a flag indicating whether any requested kernel function is allowed to be called.</returns>
    private protected (IReadOnlyList<KernelFunction>? Functions, bool AllowAnyRequestedKernelFunction) GetFunctions(IList<string>? functionFQNs, IEnumerable<KernelFunction>? functions, Kernel? kernel, bool autoInvoke)
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
        bool allowAnyRequestedKernelFunction = false;

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
                function = functions?.FirstOrDefault(f => f.Name == nameParts.Name && f.PluginName == nameParts.PluginName);
                if (function is not null)
                {
                    availableFunctions.Add(function);
                    continue;
                }

                throw new KernelException($"The specified function {functionFQN} was not found.");
            }
        }
        // Provide all functions from the kernel.
        else if (kernel is not null)
        {
            allowAnyRequestedKernelFunction = true;

            foreach (var plugin in kernel.Plugins)
            {
                (availableFunctions ??= new List<KernelFunction>(kernel.Plugins.Count)).AddRange(plugin);
            }
        }

        return new(availableFunctions, allowAnyRequestedKernelFunction);
    }
}

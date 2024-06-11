// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' function information to the model or a specified subset.
/// This behavior allows the model to decide whether to call the functions and, if so, which ones to call.
/// </summary>
internal sealed class AutoFunctionChoiceBehavior : FunctionChoiceBehavior
{
    /// <summary>
    /// List of the functions that the model can choose from.
    /// </summary>
    private readonly IEnumerable<KernelFunction>? _functions;

    /// <summary>
    /// Indicates whether the functions should be automatically invoked by the AI service/connector.
    /// </summary>
    private readonly bool _autoInvoke = true;

    /// <summary>
    /// Initializes a new instance of the <see cref="AutoFunctionChoiceBehavior"/> class.
    /// </summary>
    [JsonConstructor]
    public AutoFunctionChoiceBehavior()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AutoFunctionChoiceBehavior"/> class.
    /// </summary>
    /// <param name="autoInvoke">Indicates whether the functions should be automatically invoked by the AI service/connector.</param>
    /// <param name="functions">The subset of the <see cref="Kernel"/>'s plugins' functions to provide to the model.
    /// If null or empty, all <see cref="Kernel"/>'s plugins' functions are provided to the model.</param>
    public AutoFunctionChoiceBehavior(bool autoInvoke = true, IEnumerable<KernelFunction>? functions = null)
    {
        this._autoInvoke = autoInvoke;
        this._functions = functions;
        this.Functions = functions?.Select(f => FunctionName.ToFullyQualifiedName(f.Name, f.PluginName, FunctionNameSeparator)).ToList();
    }

    /// <summary>
    /// Fully qualified names of subset of the <see cref="Kernel"/>'s plugins' functions to provide to the model.
    /// If null or empty, all <see cref="Kernel"/>'s plugins' functions are provided to the model.
    /// </summary>
    [JsonPropertyName("functions")]
    public IList<string>? Functions { get; set; }

    /// <inheritdoc />
    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorContext context)
    {
        // If auto-invocation is specified, we need a kernel to be able to invoke the functions.
        // Lack of a kernel is fatal: we don't want to tell the model we can handle the functions
        // and then fail to do so, so we fail before we get to that point. This is an error
        // on the consumers behalf: if they specify auto-invocation with any functions, they must
        // specify the kernel and the kernel must contain those functions.
        if (this._autoInvoke && context.Kernel is null)
        {
            throw new KernelException("Auto-invocation for Auto choice behavior is not supported when no kernel is provided.");
        }

        List<KernelFunction>? availableFunctions = null;
        bool allowAnyRequestedKernelFunction = false;

        // Handle functions provided via the 'Functions' property as function fully qualified names.
        if (this.Functions is { } functionFQNs && functionFQNs.Any())
        {
            availableFunctions = [];

            foreach (var functionFQN in functionFQNs)
            {
                var nameParts = FunctionName.Parse(functionFQN, FunctionNameSeparator);

                // Check if the function is available in the kernel. If it is, then connectors can find it for auto-invocation later.
                if (context.Kernel!.Plugins.TryGetFunction(nameParts.PluginName, nameParts.Name, out var function))
                {
                    availableFunctions.Add(function);
                    continue;
                }

                // If auto-invocation is requested and no function is found in the kernel, fail early.
                if (this._autoInvoke)
                {
                    throw new KernelException($"The specified function {functionFQN} is not available in the kernel.");
                }

                // Check if the function instance was provided via the constructor for manual-invocation.
                function = this._functions?.FirstOrDefault(f => f.Name == nameParts.Name && f.PluginName == nameParts.PluginName);
                if (function is not null)
                {
                    availableFunctions.Add(function);
                    continue;
                }

                throw new KernelException($"No instance of the specified function {functionFQN} is found.");
            }
        }
        // Provide all functions from the kernel.
        else if (context.Kernel is not null)
        {
            allowAnyRequestedKernelFunction = true;

            foreach (var plugin in context.Kernel.Plugins)
            {
                availableFunctions ??= [];
                availableFunctions.AddRange(plugin);
            }
        }

        return new FunctionChoiceBehaviorConfiguration()
        {
            Choice = FunctionChoice.Auto,
            Functions = availableFunctions,
            AutoInvoke = this._autoInvoke,
            AllowAnyRequestedKernelFunction = allowAnyRequestedKernelFunction
        };
    }
}

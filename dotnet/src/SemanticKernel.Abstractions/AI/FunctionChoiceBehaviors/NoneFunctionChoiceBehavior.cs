// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' function information to the model or a specified subset.
/// This behavior forces the model to not call any functions and only generate a user-facing message.
/// </summary>
/// <remarks>
/// Although this behavior prevents the model from calling any functions, the model can use the provided function information
/// to describe how it would complete the prompt if it had the ability to call the functions.
/// </remarks>
internal sealed class NoneFunctionChoiceBehavior : FunctionChoiceBehavior
{
    /// <summary>
    /// List of the functions that the model can choose from.
    /// </summary>
    private readonly IEnumerable<KernelFunction>? _functions;

    /// <summary>
    /// The behavior options.
    /// </summary>
    private readonly FunctionChoiceBehaviorOptions _options;

    /// <summary>
    /// Initializes a new instance of the <see cref="NoneFunctionChoiceBehavior"/> class.
    /// </summary>
    [JsonConstructor]
    public NoneFunctionChoiceBehavior()
    {
        this._options = new FunctionChoiceBehaviorOptions();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="NoneFunctionChoiceBehavior"/> class.
    /// </summary>
    /// <param name="functions">The subset of the <see cref="Kernel"/>'s plugins' functions to provide to the model.
    /// <param name="options">The behavior options.</param>
    /// If null or empty, all <see cref="Kernel"/>'s plugins' functions are provided to the model.</param>
    public NoneFunctionChoiceBehavior(IEnumerable<KernelFunction>? functions, FunctionChoiceBehaviorOptions? options = null)
    {
        this._functions = functions;
        this.Functions = functions?.Select(f => FunctionName.ToFullyQualifiedName(f.Name, f.PluginName, FunctionNameSeparator)).ToList();
        this._options = options ?? new FunctionChoiceBehaviorOptions();
    }

    /// <summary>
    /// Fully qualified names of subset of the <see cref="Kernel"/>'s plugins' functions to provide to the model.
    /// If null or empty, all <see cref="Kernel"/>'s plugins' functions are provided to the model.
    /// </summary>
    [JsonPropertyName("functions")]
    public IList<string>? Functions { get; set; }

    /// <inheritdoc/>
    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorContext context)
    {
        List<KernelFunction>? availableFunctions = null;

        // Handle functions provided via the 'Functions' property as function fully qualified names.
        if (this.Functions is { } functionFQNs && functionFQNs.Any())
        {
            availableFunctions = [];

            foreach (var functionFQN in functionFQNs)
            {
                var nameParts = FunctionName.Parse(functionFQN, FunctionNameSeparator);

                // Check if the function is available in the kernel.
                if (context.Kernel!.Plugins.TryGetFunction(nameParts.PluginName, nameParts.Name, out var function))
                {
                    availableFunctions.Add(function);
                    continue;
                }

                // Check if a function instance that was not imported into the kernel was provided through the constructor.
                function = this._functions?.FirstOrDefault(f => f.Name == nameParts.Name && f.PluginName == nameParts.PluginName);
                if (function is not null)
                {
                    availableFunctions.Add(function);
                    continue;
                }

                throw new KernelException($"The specified function {functionFQN} was not found.");
            }
        }
        // Provide all functions from the kernel.
        else if (context.Kernel is not null)
        {
            foreach (var plugin in context.Kernel.Plugins)
            {
                availableFunctions ??= [];
                availableFunctions.AddRange(plugin);
            }
        }

        return new FunctionChoiceBehaviorConfiguration(this._options)
        {
            Choice = FunctionChoice.None,
            Functions = availableFunctions,
        };
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' functions to AI model to call or specific ones.
/// This behavior forces the model to always call one or more functions.
/// </summary>
internal sealed class RequiredFunctionChoiceBehavior : FunctionChoiceBehavior
{
    /// <summary>
    /// List of the functions to provide to LLM.
    /// </summary>
    private readonly IEnumerable<KernelFunction>? _functions;

    /// <summary>
    /// Indicates whether the functions should be automatically invoked by AI connectors.
    /// </summary>
    private readonly bool _autoInvoke = true;

    /// <summary>
    /// Functions selector to customize functions selection logic.
    /// </summary>
    private readonly Func<FunctionChoiceBehaviorFunctionsSelectorContext, IReadOnlyList<KernelFunction>?>? _functionsSelector;

    /// <summary>
    /// Initializes a new instance of the <see cref="RequiredFunctionChoiceBehavior"/> class.
    /// </summary>
    [JsonConstructor]
    public RequiredFunctionChoiceBehavior()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="RequiredFunctionChoiceBehavior"/> class.
    /// </summary>
    /// <param name="functions">
    /// Functions to provide to AI model. If null, all <see cref="Kernel"/>'s plugins' functions are provided to the model.
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
    public RequiredFunctionChoiceBehavior(IEnumerable<KernelFunction>? functions = null, bool autoInvoke = true, Func<FunctionChoiceBehaviorFunctionsSelectorContext, IReadOnlyList<KernelFunction>?>? functionsSelector = null)
    {
        this.Functions = functions?.Select(f => FunctionName.ToFullyQualifiedName(f.Name, f.PluginName, FunctionNameSeparator)).ToList();
        this._functions = functions;
        this._autoInvoke = autoInvoke;
        this._functionsSelector = functionsSelector;
    }

    /// <summary>
    /// Fully qualified names of the functions to provide to AI model.
    /// If null or empty, all <see cref="Kernel"/>'s plugins' functions are provided to the model.
    /// </summary>
    [JsonPropertyName("functions")]
    public IList<string>? Functions { get; set; }

    /// <inheritdoc />
#pragma warning disable SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorConfigurationContext context)
    {
        var functions = base.GetFunctions(this.Functions, this._functions, context.Kernel, this._autoInvoke);

        IReadOnlyList<KernelFunction>? selectedFunctions = null;

        // Invoke function selector, if provided, to get the final list of functions.
        if (this._functionsSelector is not null)
        {
            selectedFunctions = this._functionsSelector(new FunctionChoiceBehaviorFunctionsSelectorContext(context.ChatHistory)
            {
                Kernel = context.Kernel,
                Functions = functions,
            });
        }

        return new FunctionChoiceBehaviorConfiguration()
        {
            Choice = FunctionChoice.Required,
            Functions = selectedFunctions ?? functions,
            AutoInvoke = this._autoInvoke,
        };
#pragma warning restore SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
    }
}

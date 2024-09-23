﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' functions to AI model to call or specified ones.
/// This behavior forces the model to always call one or more functions.
/// </summary>
internal sealed class RequiredFunctionChoiceBehavior : FunctionChoiceBehavior
{
    /// <summary>
    /// Indicates whether the functions should be automatically invoked by AI connectors.
    /// </summary>
    private readonly bool _autoInvoke = true;

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
    /// <param name="options">The behavior options.</param>
    public RequiredFunctionChoiceBehavior(
        IEnumerable<KernelFunction>? functions = null,
        bool autoInvoke = true,
        FunctionChoiceBehaviorOptions? options = null) : base(functions)
    {
        this.Functions = functions?.Select(f => FunctionName.ToFullyQualifiedName(f.Name, f.PluginName, FunctionNameSeparator)).ToList();
        this._autoInvoke = autoInvoke;
        this.Options = options;
    }

    /// <summary>
    /// Fully qualified names of the functions to provide to AI model.
    /// If null, all <see cref="Kernel"/>'s plugins' functions are provided to the model.
    /// If empty, no functions are provided to the model, which is equivalent to disabling function calling.
    /// </summary>
    [JsonPropertyName("functions")]
    public IList<string>? Functions { get; set; }

    /// <summary>
    /// The behavior options.
    /// </summary>
    [JsonPropertyName("options")]
    public FunctionChoiceBehaviorOptions? Options { get; set; }

    /// <inheritdoc />
    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorConfigurationContext context)
    {
        // Stop advertising functions after the first request to prevent the AI model from repeatedly calling the same function.
        // This is a temporary solution which will be removed after we have a way to dynamically control list of functions to advertise to the model.
        if (context.RequestSequenceIndex >= 1)
        {
            return new FunctionChoiceBehaviorConfiguration(this.Options ?? DefaultOptions)
            {
                Choice = FunctionChoice.Required,
                Functions = null,
                AutoInvoke = this._autoInvoke,
            };
        }

        var functions = base.GetFunctions(this.Functions, context.Kernel, this._autoInvoke);

        IReadOnlyList<KernelFunction>? selectedFunctions = null;

        return new FunctionChoiceBehaviorConfiguration(this.Options ?? DefaultOptions)
        {
            Choice = FunctionChoice.Required,
            Functions = selectedFunctions ?? functions,
            AutoInvoke = this._autoInvoke,
        };
    }
}

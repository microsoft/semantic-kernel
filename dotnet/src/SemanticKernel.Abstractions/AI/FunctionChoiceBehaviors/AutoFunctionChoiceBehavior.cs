﻿// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' functions to AI model to call or specified ones.
/// This behavior allows the model to decide whether to call the functions and, if so, which ones to call.
/// </summary>
internal sealed class AutoFunctionChoiceBehavior : FunctionChoiceBehavior
{
    /// <summary>
    /// Indicates whether the functions should be automatically invoked by AI connectors.
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
    /// <param name="functions">
    /// Functions to provide to AI model. If null, all <see cref="Kernel"/>'s plugins' functions are provided to the model.
    /// If empty, no functions are provided to the model, which is equivalent to disabling function calling.
    /// </param>
    /// <param name="autoInvoke">
    /// Indicates whether the functions should be automatically invoked by AI connectors.
    /// </param>
    /// <param name="options">The behavior options.</param>
    public AutoFunctionChoiceBehavior(IEnumerable<KernelFunction>? functions = null, bool autoInvoke = true, FunctionChoiceBehaviorOptions? options = null) : base(functions)
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
        var functions = base.GetFunctions(this.Functions, context.Kernel, this._autoInvoke);

        return new FunctionChoiceBehaviorConfiguration(this.Options ?? DefaultOptions)
        {
            Choice = FunctionChoice.Auto,
            Functions = functions,
            AutoInvoke = this._autoInvoke,
        };
    }
}

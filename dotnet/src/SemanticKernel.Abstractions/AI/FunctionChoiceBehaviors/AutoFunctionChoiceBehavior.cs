// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents a <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' functions to the LLM to call or specific ones.
/// This behavior allows the LLM to decide whether to call the functions and, if so, which ones to call.
/// </summary>
internal sealed class AutoFunctionChoiceBehavior : FunctionChoiceBehavior
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
    /// Functions to provide to LLM. If null, all <see cref="Kernel"/>'s plugins' functions are provided to LLM.
    /// If empty, no functions are provided to LLM, which is equivalent to disabling function calling.
    /// </param>
    /// <param name="autoInvoke">
    /// Indicates whether the functions should be automatically invoked by AI connectors.
    /// </param>
    public AutoFunctionChoiceBehavior(IEnumerable<KernelFunction>? functions = null, bool autoInvoke = true)
    {
        this.Functions = functions?.Select(f => FunctionName.ToFullyQualifiedName(f.Name, f.PluginName, FunctionNameSeparator)).ToList();
        this._functions = functions;
        this._autoInvoke = autoInvoke;
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

        return new FunctionChoiceBehaviorConfiguration()
        {
            Choice = FunctionChoice.Auto,
            Functions = functions,
            AutoInvoke = this._autoInvoke,
        };
#pragma warning restore SKEXP0001 // Type is for evaluation purposes only and is subject to change or removal in future updates. Suppress this diagnostic to proceed.
    }
}

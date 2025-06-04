// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents <see cref="FunctionChoiceBehavior"/> that provides either all of the <see cref="Kernel"/>'s plugins' functions to AI model to call or specified ones but instructs it not to call any of them.
/// The model may use the provided function in the response it generates. E.g. the model may describe which functions it would call and with what parameter values.
/// This response is useful if the user should first validate what functions the model will use.
/// </summary>
public sealed class NoneFunctionChoiceBehavior : FunctionChoiceBehavior
{
    /// <summary>
    /// Initializes a new instance of the <see cref="NoneFunctionChoiceBehavior"/> class.
    /// </summary>
    [JsonConstructor]
    internal NoneFunctionChoiceBehavior()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="NoneFunctionChoiceBehavior"/> class.
    /// </summary>
    /// <param name="functions">
    /// Functions to provide to AI model. If null, all <see cref="Kernel"/>'s plugins' functions are provided to the model.
    /// If empty, no functions are provided to the model.
    /// </param>
    /// <param name="options">The behavior options.</param>
    internal NoneFunctionChoiceBehavior(IEnumerable<KernelFunction>? functions = null, FunctionChoiceBehaviorOptions? options = null) : base(functions)
    {
        this.Functions = functions?.Select(f => FunctionName.ToFullyQualifiedName(f.Name, f.PluginName, FunctionNameSeparator)).ToList();
        this.Options = options;
    }

    /// <summary>
    /// Fully qualified names of the functions to provide to AI model.
    /// If null, all <see cref="Kernel"/>'s plugins' functions are provided to the model.
    /// If empty, no functions are provided to the model, which is equivalent to disabling function calling.
    /// </summary>
    [JsonPropertyName("functions")]
#pragma warning disable CA1721 // Property names should not match get methods. Both Functions property and GetFunctions method are needed.
    public IList<string>? Functions { get; set; }
#pragma warning restore CA1721 // Property names should not match get methods. Both Functions property and GetFunctions method are needed.

    /// <summary>
    /// The behavior options.
    /// </summary>
    [JsonPropertyName("options")]
    public FunctionChoiceBehaviorOptions? Options { get; set; }

    /// <inheritdoc />
    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorConfigurationContext context)
    {
        var functions = base.GetFunctions(this.Functions, context.Kernel, autoInvoke: false);

        return new FunctionChoiceBehaviorConfiguration(this.Options ?? DefaultOptions)
        {
            Choice = FunctionChoice.None,
            Functions = functions,
            AutoInvoke = false,
        };
    }
}

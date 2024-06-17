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
    /// The behavior options.
    /// </summary>
    private readonly FunctionChoiceBehaviorOptions _options;

    /// <summary>
    /// Initializes a new instance of the <see cref="AutoFunctionChoiceBehavior"/> class.
    /// </summary>
    [JsonConstructor]
    public AutoFunctionChoiceBehavior()
    {
        this._options = new FunctionChoiceBehaviorOptions();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AutoFunctionChoiceBehavior"/> class.
    /// </summary>
    /// <param name="functions">The subset of the <see cref="Kernel"/>'s plugins' functions to provide to the model.
    /// If null or empty, all <see cref="Kernel"/>'s plugins' functions are provided to the model.</param>
    /// <param name="options">The behavior options.</param>
    public AutoFunctionChoiceBehavior(IEnumerable<KernelFunction>? functions = null, FunctionChoiceBehaviorOptions? options = null)
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

    /// <inheritdoc />
    public override FunctionChoiceBehaviorConfiguration GetConfiguration(FunctionChoiceBehaviorContext context)
    {
        (IReadOnlyList<KernelFunction>? functions, bool allowAnyRequestedKernelFunction) = base.GetFunctions(this.Functions, this._functions, context.Kernel, this._options.AutoInvoke);

        return new FunctionChoiceBehaviorConfiguration(this._options)
        {
            Choice = FunctionChoice.Auto,
            Functions = functions,
            AllowAnyRequestedKernelFunction = allowAnyRequestedKernelFunction
        };
    }
}

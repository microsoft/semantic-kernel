// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Function result after execution.
/// </summary>
public sealed class FunctionResult
{
    /// <summary>
    /// Name of executed function.
    /// </summary>
    public string FunctionName { get; internal set; }

    /// <summary>
    /// Name of the plugin containing the function.
    /// </summary>
    public string PluginName { get; internal set; }

    /// <summary>
    /// Metadata for storing additional information about function execution result.
    /// </summary>
    public Dictionary<string, object> Metadata { get; internal set; } = new Dictionary<string, object>();

    /// <summary>
    /// Function result object.
    /// </summary>
    internal object? Value { get; private set; } = null;

    /// <summary>
    /// Instance of <see cref="SKContext"/> to pass in function pipeline.
    /// </summary>
    internal SKContext Context { get; private set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionResult"/> class.
    /// </summary>
    /// <param name="functionName">Name of executed function.</param>
    /// <param name="pluginName">Name of the plugin containing the function.</param>
    /// <param name="context">Instance of <see cref="SKContext"/> to pass in function pipeline.</param>
    public FunctionResult(string functionName, string pluginName, SKContext context)
    {
        this.FunctionName = functionName;
        this.PluginName = pluginName;
        this.Context = context;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionResult"/> class.
    /// </summary>
    /// <param name="functionName">Name of executed function.</param>
    /// <param name="pluginName">Name of the plugin containing the function.</param>
    /// <param name="context">Instance of <see cref="SKContext"/> to pass in function pipeline.</param>
    /// <param name="value">Function result object.</param>
    public FunctionResult(string functionName, string pluginName, SKContext context, object? value)
        : this(functionName, pluginName, context)
    {
        this.Value = value;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionResult"/> class.
    /// </summary>
    /// <param name="functionName">Name of executed function.</param>
    /// <param name="pluginName">Name of the plugin containing the function.</param>
    /// <param name="context">Instance of <see cref="SKContext"/> to pass in function pipeline.</param>
    /// <param name="value">Function result object.</param>
    /// <param name="modelResults">Collection of <see cref="ModelResult"/> records.</param>
    public FunctionResult(string functionName, string pluginName, SKContext context, object? value, IReadOnlyCollection<ModelResult> modelResults)
        : this(functionName, pluginName, context, value)
    {
        this.AddModelResults(modelResults);
    }

    /// <summary>
    /// Returns function result value.
    /// </summary>
    /// <typeparam name="T">Target type for result value casting.</typeparam>
    /// <exception cref="InvalidCastException">Thrown when it's not possible to cast result value to <typeparamref name="T"/>.</exception>
    public T? GetValue<T>()
    {
        if (this.Value is null)
        {
            return default;
        }

        if (this.Value is T typedResult)
        {
            return typedResult;
        }

        throw new InvalidCastException($"Cannot cast {this.Value.GetType()} to {typeof(T)}");
    }
}

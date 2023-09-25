// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

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
    /// <remarks>
    /// Getting this property will block await until the streaming completes as SKContext needs the full result.
    /// </remarks>
    internal SKContext Context => this.GetResultingSKContext();

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
        this._inputContext = context;
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

        if (this.Value is IAsyncEnumerable<string> asyncEnumerableString)
        {
            return (T)(object)this.ReadAllTextStreaming(asyncEnumerableString);
        }

        throw new InvalidCastException($"Cannot cast {this.Value.GetType()} to {typeof(T)}");
    }

    private SKContext _inputContext;
    private SKContext? _outputContext = null;

    /// <summary>
    /// Gets the resulting context lazily.
    /// This will block await until the streaming completes as SKContext uses the full result to return.
    /// </summary>
    /// <returns></returns>
    /// <exception cref="NotSupportedException"></exception>
    private SKContext GetResultingSKContext()
    {
        if (this._outputContext is not null)
        {
            return this._outputContext;
        }

        this._outputContext = this._inputContext.Clone();

        // No return value, just return the non modified context
        if (this.Value is null)
        {
            return this._outputContext;
        }

        string fullResult;
        if (this.Value is string)
        {
            fullResult = this.GetValue<string>()!;
        }
        else if (this.Value is IAsyncEnumerable<string> streamingValues)
        {
            fullResult = this.ReadAllTextStreaming(streamingValues);
        }
        else
        {
            fullResult = Convert.ToString(this.Value, this._outputContext.Culture);
        }

        this._outputContext.Variables.Update(fullResult);

        return this._outputContext;
    }

    private string ReadAllTextStreaming(IAsyncEnumerable<string> streamingValues)
    {
        StringBuilder fullResult = new();
        foreach (var token in streamingValues.ToEnumerable())
        {
            fullResult.Append(token);
        }

        return fullResult.ToString();
    }
}

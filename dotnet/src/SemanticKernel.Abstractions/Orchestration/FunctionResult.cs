// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Function result after execution.
/// </summary>
public sealed class FunctionResult
{
    internal Dictionary<string, object>? _metadata;

    /// <summary>
    /// Name of executed function.
    /// </summary>
    public string FunctionName { get; internal set; }

    /// <summary>
    /// Return true if the function result is for a function that was cancelled.
    /// </summary>
    public bool IsCancellationRequested { get; internal set; }

    /// <summary>
    /// Return true if the function should be skipped.
    /// </summary>
    public bool IsSkipRequested { get; internal set; }

    /// <summary>
    /// Return true if the function should be repeated.
    /// </summary>
    public bool IsRepeatRequested { get; internal set; }

    /// <summary>
    /// Metadata for storing additional information about function execution result.
    /// </summary>
    public Dictionary<string, object> Metadata
    {
        get => this._metadata ??= new();
        internal set => this._metadata = value;
    }

    /// <summary>
    /// Function result object.
    /// </summary>
    internal object? Value { get; private set; } = null;

    /// <summary>
    /// Instance of <see cref="ContextVariables"/> to pass in function pipeline.
    /// </summary>
    internal ContextVariables Variables { get; private set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionResult"/> class.
    /// </summary>
    /// <param name="functionName">Name of executed function.</param>
    /// <param name="variables">Instance of <see cref="ContextVariables"/> to pass in function pipeline.</param>
    public FunctionResult(string functionName, ContextVariables variables)
    {
        this.FunctionName = functionName;
        this.Variables = variables;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionResult"/> class.
    /// </summary>
    /// <param name="functionName">Name of executed function.</param>
    /// <param name="variables">Instance of <see cref="ContextVariables"/> to pass in function pipeline.</param>
    /// <param name="value">Function result object.</param>
    public FunctionResult(string functionName, ContextVariables variables, object? value)
        : this(functionName, variables)
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

        throw new InvalidCastException($"Cannot cast {this.Value.GetType()} to {typeof(T)}");
    }

    /// <summary>
    /// Get typed value from metadata.
    /// </summary>
    public bool TryGetMetadataValue<T>(string key, out T value)
    {
        if (this._metadata is { } metadata &&
            metadata.TryGetValue(key, out object? valueObject) &&
            valueObject is T typedValue)
        {
            value = typedValue;
            return true;
        }

        value = default!;
        return false;
    }

    /// <inheritdoc/>
    public override string ToString() => this.Value?.ToString() ?? base.ToString();
}

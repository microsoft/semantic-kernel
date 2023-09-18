// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Function result after execution.
/// </summary>
public sealed class FunctionResult
{
    /// <summary>
    /// Additional data from model.
    /// </summary>
    public IReadOnlyCollection<ModelResult> ModelResults { get; internal set; } = Array.Empty<ModelResult>();

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
    /// <param name="context">Instance of <see cref="SKContext"/> to pass in function pipeline.</param>
    public FunctionResult(SKContext context)
    {
        this.Context = context;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionResult"/> class.
    /// </summary>
    /// <param name="context">Instance of <see cref="SKContext"/> to pass in function pipeline.</param>
    /// <param name="value">Function result object.</param>
    public FunctionResult(SKContext context, object? value)
    {
        this.Value = value;
        this.Context = context;
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

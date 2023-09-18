// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Kernel result after execution.
/// </summary>
public sealed class KernelResult
{
    /// <summary>
    /// Additional data from model.
    /// </summary>
    public IReadOnlyCollection<ModelResult> ModelResults { get; internal set; } = Array.Empty<ModelResult>();

    /// <summary>
    /// Kernel result object.
    /// </summary>
    internal object? Value { get; private set; } = null;

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
    /// Creates instance of <see cref="KernelResult"/> from instance of <see cref="FunctionResult"/>.
    /// </summary>
    /// <param name="functionResult">Instance of <see cref="FunctionResult"/>.</param>
    internal static KernelResult FromFunctionResult(FunctionResult functionResult)
    {
        return new KernelResult
        {
            Value = functionResult.Value,
            ModelResults = functionResult.ModelResults
        };
    }
}

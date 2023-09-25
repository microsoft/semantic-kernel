// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Kernel result after execution.
/// </summary>
public sealed class KernelResult
{
    /// <summary>
    /// Results from all functions in pipeline.
    /// </summary>
    public IReadOnlyCollection<FunctionResult> FunctionResults { get; internal set; } = Array.Empty<FunctionResult>();

    /// <summary>
    /// Kernel result object.
    /// </summary>
    internal object? Value { get; private set; } = null;

    /// <summary>
    /// Returns kernel result value.
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

        // Retro-compatibility with legacy non streaming functions
        if (this.Value is IAsyncEnumerable<string> asyncEnumerableString)
        {
            return (T)(object)this.ReadAllTextStreaming(asyncEnumerableString);
        }

        throw new InvalidCastException($"Cannot cast {this.Value.GetType()} to {typeof(T)}");
    }

    /// <summary>
    /// Creates instance of <see cref="KernelResult"/> based on function results.
    /// </summary>
    /// <param name="value">Kernel result object.</param>
    /// <param name="functionResults">Results from all functions in pipeline.</param>
    public static KernelResult FromFunctionResults(object? value, IReadOnlyCollection<FunctionResult> functionResults)
    {
        return new KernelResult
        {
            Value = value,
            FunctionResults = functionResults
        };
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

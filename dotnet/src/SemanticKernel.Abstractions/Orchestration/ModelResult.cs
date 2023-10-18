// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

#pragma warning disable CA1024

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Represents a result from a model execution.
/// </summary>
public sealed class ModelResult
{
    private readonly object _result;

    /// <summary>
    /// Initializes a new instance of the <see cref="ModelResult"/> class with the specified result object.
    /// </summary>
    /// <param name="result">The result object to be stored in the ModelResult instance.</param>
    public ModelResult(object result)
    {
        Verify.NotNull(result);

        this._result = result;
    }

    /// <summary>
    /// Gets the raw result object stored in the <see cref="ModelResult"/>instance.
    /// </summary>
    /// <returns>The raw result object.</returns>
    public object GetRawResult() => this._result;

    /// <summary>
    /// Gets the result object stored in the <see cref="ModelResult"/> instance, cast to the specified type.
    /// </summary>
    /// <typeparam name="T">The type to cast the result object to.</typeparam>
    /// <returns>The result object cast to the specified type.</returns>
    /// <exception cref="InvalidCastException">Thrown when the result object cannot be cast to the specified type.</exception>
    public T GetResult<T>()
    {
        if (this._result is T typedResult)
        {
            return typedResult;
        }

        throw new InvalidCastException($"Cannot cast {this._result.GetType()} to {typeof(T)}");
    }

    /// <summary>
    /// Gets the result object stored in the ModelResult instance as a JSON element.
    /// </summary>
    /// <returns>The result object as a JSON element.</returns>
    public JsonElement GetJsonResult()
    {
        return Json.Deserialize<JsonElement>(Json.Serialize(this._result));
    }
}

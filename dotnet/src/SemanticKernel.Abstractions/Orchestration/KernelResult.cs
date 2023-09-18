// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Orchestration;

public sealed class KernelResult
{
    public IReadOnlyCollection<ModelResult> ModelResults { get; internal set; } = Array.Empty<ModelResult>();

    internal object? Value { get; private set; } = null;

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

    internal static KernelResult FromFunctionResult(FunctionResult functionResult)
    {
        return new KernelResult
        {
            Value = functionResult.Value,
            ModelResults = functionResult.ModelResults
        };
    }
}

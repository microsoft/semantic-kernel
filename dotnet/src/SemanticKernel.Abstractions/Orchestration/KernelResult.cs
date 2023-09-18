// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System;

namespace Microsoft.SemanticKernel.Orchestration;

public sealed class KernelResult
{
    public IReadOnlyCollection<ModelResult> ModelResults { get; set; } = Array.Empty<ModelResult>();

    public object? Value { get; private set; } = null;

    public T GetValue<T>()
    {
        if (this.Value is T typedResult)
        {
            return typedResult;
        }

        throw new InvalidCastException($"Cannot cast {this.Value!.GetType()} to {typeof(T)}");
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

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Orchestration;

public sealed class FunctionResult
{
    public IReadOnlyCollection<ModelResult> ModelResults { get; internal set; } = Array.Empty<ModelResult>();

    internal object? Value { get; private set; } = null;

    internal SKContext Context { get; private set; }

    public FunctionResult(SKContext context)
    {
        this.Context = context;
    }

    public FunctionResult(SKContext context, object? value)
    {
        this.Value = value;
        this.Context = context;
    }

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

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Text;

#pragma warning disable CA1024

namespace Microsoft.SemanticKernel.Orchestration;
public sealed class ModelResult
{
    private readonly object result;

    public ModelResult(object result)
    {
        Verify.NotNull(result);

        this.result = result;
    }

    public object GetRawResult() => this.result;

    public T GetResult<T>()
    {
        if (this.result is T typedResult)
        {
            return typedResult;
        }

        throw new InvalidCastException($"Cannot cast {this.result.GetType()} to {typeof(T)}");
    }

    public JsonElement GetJsonResult()
    {
        return Json.Deserialize<JsonElement>(this.result.ToJson());
    }
}

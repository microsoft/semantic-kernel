// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of SKContext
namespace Microsoft.SemanticKernel;

public static class OpenAISKContextExtensions
{
    private static IEnumerable<Completions>? GetOpenAILastResultData(this SKContext skContext)
    {
        if (skContext.LastResultData is not null)
        {
            return skContext.LastResultData.Deserialize<Completions[]>();
        }

        return null;
    }
}

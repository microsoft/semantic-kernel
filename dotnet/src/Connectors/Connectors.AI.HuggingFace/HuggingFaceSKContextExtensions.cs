// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of SKContext
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

public static class HuggingFaceSKContextExtensions
{
    private static IEnumerable<TextCompletionResponse>? GetHuggingFaceLastResultData(this SKContext skContext)
    {
        if (skContext.LastResultData is not null)
        {
            return skContext.LastResultData.Deserialize<TextCompletionResponse[]>();
        }

        return null;
    }
}

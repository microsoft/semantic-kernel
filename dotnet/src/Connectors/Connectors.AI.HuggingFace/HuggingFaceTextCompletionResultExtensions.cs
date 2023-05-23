// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of SKContext
namespace Microsoft.SemanticKernel.AI.TextCompletion;

public static class HuggingFaceTextCompletionResultExtensions
{
    public static TextCompletionResponse? GetHuggingFaceLastResultData(this ITextCompletionResult textResult)
    {
        return textResult.ResultData as TextCompletionResponse;
    }
}

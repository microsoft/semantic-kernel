// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of SKContext
namespace Microsoft.SemanticKernel.AI.TextCompletion;

public static class OpenAITextCompletionResultExtensions
{
    public static Completions? GetOpenAILastResultData(this ITextCompletionResult textResult)
    {
        return textResult.ResultData as Completions;
    }
}

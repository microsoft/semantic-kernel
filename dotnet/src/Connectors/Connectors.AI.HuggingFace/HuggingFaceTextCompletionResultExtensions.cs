// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of SKContext
namespace Microsoft.SemanticKernel.AI.TextCompletion;

public static class HuggingFaceTextCompletionResultExtensions
{
    /// <summary>
    /// Gets the model result data as a traversable <see cref="TextCompletionResponse"/>.
    /// </summary>
    /// <param name="textResult">Target extended interface</param>
    /// <returns>Result data as <see cref="TextCompletionResponse"/></returns>
    public static TextCompletionResponse? GetHuggingFaceLastResultData(this ITextCompletionResult textResult)
    {
        return textResult.ResultData as TextCompletionResponse;
    }
}

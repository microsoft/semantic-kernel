// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of SKContext
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

public static class HuggingFaceSKContextExtensions
{
    /// <summary>
    /// Retrieves a list of <see cref="TextCompletionResponse"/> from <see cref="SKContext.LastPromptResults"/>.
    /// </summary>
    /// <param name="skContext">Current context</param>
    /// <returns>List of <see cref="TextCompletionResponse"/></returns>
    public static IEnumerable<TextCompletionResponse>? GetHuggingFaceLastResultsData(this SKContext skContext)
    {
        if (skContext.LastPromptResults is not null)
        {
            return (skContext.LastPromptResults as object[])?.OfType<TextCompletionResponse>();
        }

        return null;
    }

    /// <summary>
    /// Retrieves the first occurrence of <see cref="TextCompletionResponse"/> from <see cref="SKContext.LastPromptResults"/>.
    /// </summary>
    /// <param name="skContext">Target SK Context</param>
    /// <returns>First occurrence of <see cref="TextCompletionResponse"/></returns>
    public static TextCompletionResponse? GetHuggingFaceLastResultData(this SKContext skContext)
    {
        return GetHuggingFaceLastResultsData(skContext)?.FirstOrDefault();
    }
}

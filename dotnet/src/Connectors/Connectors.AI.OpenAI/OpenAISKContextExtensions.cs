// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of SKContext
namespace Microsoft.SemanticKernel;

public static class OpenAISKContextExtensions
{
    /// <summary>
    /// Retrieves a list of <see cref="Completions"/> from <see cref="SKContext.LastPromptResults"/>.
    /// </summary>
    /// <param name="skContext">Current context</param>
    /// <returns>List of <see cref="Completions"/></returns>
    public static IEnumerable<Completions>? GetOpenAILastPromptResults(this SKContext skContext)
    {
        if (skContext.LastPromptResults is not null)
        {
            return (skContext.LastPromptResults as object[])?.OfType<Completions>();
        }

        return null;
    }

    /// <summary>
    /// Retrieves the first occurrence of <see cref="Completions"/> from <see cref="SKContext.LastPromptResults"/>.
    /// </summary>
    /// <param name="skContext">Current context</param>
    /// <returns>First occurrence of <see cref="Completions"/></returns>
    public static Completions? GetOpenAILastPromptResult(this SKContext skContext)
    {
        return GetOpenAILastPromptResults(skContext)?.FirstOrDefault();
    }
}

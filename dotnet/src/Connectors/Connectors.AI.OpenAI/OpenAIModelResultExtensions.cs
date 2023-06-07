// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130

namespace Microsoft.SemanticKernel;

public static class OpenAIModelResultExtension
{
    /// <summary>
    /// Retrieves a typed <see cref="Completions"/> OpenAI / AzureOpenAI result from PromptResult/>.
    /// </summary>
    /// <param name="resultBase">Current context</param>
    /// <returns>OpenAI / AzureOpenAI result<see cref="Completions"/></returns>
    public static Completions GetOpenAIResult(this ModelResult resultBase)
    {
        return resultBase.GetResult<Completions>();
    }
}

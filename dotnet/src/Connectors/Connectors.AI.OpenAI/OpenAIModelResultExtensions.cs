// Copyright (c) Microsoft. All rights reserved.

using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130

namespace Microsoft.SemanticKernel;

public static class OpenAIModelResultExtension
{
    /// <summary>
    /// Retrieves a typed <see cref="Completions"/> OpenAI / AzureOpenAI result from text completion prompt.
    /// </summary>
    /// <param name="resultBase">Current context</param>
    /// <returns>OpenAI / AzureOpenAI result<see cref="Completions"/></returns>
    public static Completions GetOpenAITextResult(this ModelResult resultBase)
    {
        return resultBase.GetResult<Completions>();
    }

    /// <summary>
    /// Retrieves a typed <see cref="ChatCompletions"/> OpenAI / AzureOpenAI result from chat completion prompt.
    /// </summary>
    /// <param name="resultBase">Current context</param>
    /// <returns>OpenAI / AzureOpenAI result<see cref="ChatCompletions"/></returns>
    public static ChatCompletions GetOpenAIChatResult(this ModelResult resultBase)
    {
        return resultBase.GetResult<ChatCompletions>();
    }
}

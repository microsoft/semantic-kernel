// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.AI.PaLM.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130

namespace Microsoft.SemanticKernel;

public static class PaLMModelResultExtension
{
    /// <summary>
    /// Retrieves a typed <see cref="TextCompletionResponse"/> PaLM result from PromptResult/>.
    /// </summary>
    /// <param name="resultBase">Current context</param>
    /// <returns>PaLM result <see cref="TextCompletionResponse"/></returns>
    public static TextCompletionResponse GetPaLMResult(this ModelResult resultBase)
    {
        return resultBase.GetResult<TextCompletionResponse>();
    }
}

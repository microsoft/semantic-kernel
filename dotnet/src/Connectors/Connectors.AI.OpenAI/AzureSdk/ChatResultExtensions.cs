// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.ChatCompletion;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI;
#pragma warning restore IDE0130 // Namespace does not match folder structure

/// <summary>
/// Provides extension methods for the IChatResult interface.
/// </summary>
public static class ChatResultExtensions
{
    /// <summary>
    /// Retrieve the resulting function from the chat result.
    /// </summary>
    /// <param name="chatResult"></param>
    /// <returns>The <see cref="OpenAIFunctionResponse"/>, or null if no function was returned by the model.</returns>
    public static OpenAIFunctionResponse? GetOpenAIFunctionResponse(this IChatResult chatResult)
    {
        OpenAIFunctionResponse? functionResponse = null;
        var functionCall = chatResult.ModelResult.GetResult<ChatModelResult>().Choice.Message.FunctionCall;
        if (functionCall is not null)
        {
            functionResponse = OpenAIFunctionResponse.FromFunctionCall(functionCall);
        }
        return functionResponse;
    }
}

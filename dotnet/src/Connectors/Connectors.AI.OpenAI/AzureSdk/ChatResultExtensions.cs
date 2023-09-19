// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Provides extension methods for the IChatResult interface.
/// </summary>
public static class ChatResultExtensions
{
    /// <summary>
    /// Retrieve the resulting function from the chat result.
    /// </summary>
    /// <param name="chatResult"></param>
    /// <returns>The <see cref="OpenAIFunctionResult"/>, or null if no function was returned by the model.</returns>
    public static OpenAIFunctionResult? GetFunctionResult(this IChatResult chatResult)
    {
        OpenAIFunctionResult? functionResult = null;
        var functionCall = chatResult.ModelResult.GetResult<ChatModelResult>().Choice.Message.FunctionCall;
        if (functionCall is not null)
        {
            functionResult = OpenAIFunctionResult.FromFunctionCall(functionCall);
        }
        return functionResult;
    }
}

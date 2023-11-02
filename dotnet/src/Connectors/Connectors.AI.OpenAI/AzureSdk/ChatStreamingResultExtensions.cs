// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Provides extension methods for the IChatStreamingResult interface.
/// </summary>
public static class ChatStreamingResultExtensions
{
    /// <summary>
    /// Retrieve the resulting function from the chat result.
    /// </summary>
    /// <param name="chatStreamingResult">Chat streaming result</param>
    /// <returns>The <see cref="OpenAIFunctionResponse"/>, or null if no function was returned by the model.</returns>
    public static async Task<OpenAIFunctionResponse?> GetOpenAIStreamingFunctionResponseAsync(this IChatStreamingResult chatStreamingResult)
    {
        if (chatStreamingResult is not ChatStreamingResult)
        {
            throw new NotSupportedException($"Chat streaming result is not OpenAI {nameof(ChatStreamingResult)} supported type");
        }

        StringBuilder arguments = new();
        FunctionCall? functionCall = null;
        await foreach (SKChatMessage message in chatStreamingResult.GetStreamingChatMessageAsync())
        {
            functionCall ??= message.FunctionCall;

            arguments.Append(message.FunctionCall.Arguments);
        }

        if (functionCall is null)
        {
            return null;
        }

        functionCall.Arguments = arguments.ToString();
        return OpenAIFunctionResponse.FromFunctionCall(functionCall);
    }
}

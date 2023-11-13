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
        string? functionName = null;

        // When streaming functionCall come in bits and we need to aggregate them
        await foreach (SKChatMessage message in chatStreamingResult.GetStreamingChatMessageAsync())
        {
            if (message.FunctionCall is not null)
            {
                functionName ??= message.FunctionCall.Name;
                arguments.Append(message.FunctionCall.Arguments);
            }
        }

        // No function call was returned by the model
        if (functionName is null)
        {
            return null;
        }

        // Fully built function call
        var functionCall = new FunctionCall(functionName, arguments.ToString());

        return OpenAIFunctionResponse.FromFunctionCall(functionCall);
    }
}

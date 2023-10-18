// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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
    /// <returns>The <see cref="OpenAIFunctionResponse"/>, or null if no function was returned by the model.</returns>
    public static OpenAIFunctionResponse? GetFunctionResponse(this IChatResult chatResult)
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
    public static async IAsyncEnumerable<OpenAIFunctionResponse?> GetStreamingFunctionResponseAsync(this IChatStreamingResult chatStreamingResult)
    {
        if (chatStreamingResult is not ChatStreamingResult)
        {
            throw new NotSupportedException($"Chat streaming result is not the {nameof(ChatStreamingResult)} supported type");
        }

        await foreach (SKChatMessage message in chatStreamingResult.GetStreamingChatMessageAsync())
        {
            yield return OpenAIFunctionResponse.FromFunctionCall(message.FunctionCall);
        }
    }
}

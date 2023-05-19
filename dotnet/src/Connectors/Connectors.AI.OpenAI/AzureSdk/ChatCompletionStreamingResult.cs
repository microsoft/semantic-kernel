// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal sealed class ChatCompletionStreamingResult : IChatCompletionStreamingResult
{
    private readonly StreamingChatChoice _choice;

    public ChatCompletionStreamingResult(StreamingChatChoice choice)
    {
        this._choice = choice;
    }

    /// <inheritdoc/>
    public async Task<IChatMessage> GetChatMessageAsync(CancellationToken cancellationToken = default)
    {
        ChatMessage? chatMessage = null;
        await foreach (var message in this._choice.GetMessageStreaming(cancellationToken))
        {
            // As it loops thru the stream, the return ChatMessage is an updated/concatenated version of the previous ChatMessage
            chatMessage = message;
        }
        // As it leaves the streaming loop, the return ChatMessage is the final version of the ChatMessage to present in a non-streaming behavior

        if (chatMessage is null)
        {
            throw new AIException(AIException.ErrorCodes.UnknownError);
        }

        return new ChatMessageAdapter(chatMessage);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<IChatMessage> GetChatMessageStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var message in this._choice.GetMessageStreaming(cancellationToken))
        {
            yield return new ChatMessageAdapter(message);
        }
    }
}

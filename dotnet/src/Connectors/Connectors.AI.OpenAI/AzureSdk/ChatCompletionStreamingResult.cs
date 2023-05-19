// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal sealed class ChatCompletionStreamingResult : IChatCompletionStreamingResult, ITextCompletionStreamingResult
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

    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        return (await this.GetChatMessageAsync(cancellationToken).ConfigureAwait(false)).Content;
    }

    public async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (IChatMessage result in this.GetChatMessageStreamingAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return result.Content;
        }
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using SKChatMessage = Microsoft.SemanticKernel.AI.ChatCompletion.ChatMessage;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal sealed class ChatStreamingResult : IChatStreamingResult, ITextCompletionStreamingResult
{
    private readonly StreamingChatChoice _choice;

    public ChatStreamingResult(StreamingChatChoice choice)
    {
        this._choice = choice;
    }

    /// <inheritdoc/>
    public async Task<SemanticKernel.AI.ChatCompletion.ChatMessage> GetChatMessageAsync(CancellationToken cancellationToken = default)
    {
        var chatMessage = await this._choice.GetMessageStreaming(cancellationToken)
                                                .LastOrDefaultAsync(cancellationToken)
                                                .ConfigureAwait(false);

        if (chatMessage is null)
        {
            throw new AIException(AIException.ErrorCodes.UnknownError);
        }

        return new OpenAIChatMessage(chatMessage);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<SKChatMessage> GetChatMessageStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var message in this._choice.GetMessageStreaming(cancellationToken))
        {
            yield return new OpenAIChatMessage(message);
        }
    }

    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        return (await this.GetChatMessageAsync(cancellationToken).ConfigureAwait(false)).Content;
    }

    public async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var result in this.GetChatMessageStreamingAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return result.Content;
        }
    }
}

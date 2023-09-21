// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

internal sealed class ChatWithDataStreamingResult : IChatStreamingResult, ITextStreamingResult
{
    public ModelResult ModelResult { get; }

    public ChatWithDataStreamingResult(ChatWithDataStreamingResponse response, ChatWithDataStreamingChoice choice)
    {
        Verify.NotNull(response);
        Verify.NotNull(choice);

        this.ModelResult = new(new ChatWithDataModelResult(response.Id, DateTimeOffset.FromUnixTimeSeconds(response.Created))
        {
            ToolContent = this.GetToolContent(choice)
        });

        this._choice = choice;
    }

    public async Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
    {
        var message = this._choice.Messages.FirstOrDefault(this.IsValidMessage);

        var result = new SKChatMessage(AuthorRole.Assistant.Label, message?.Delta?.Content ?? string.Empty);

        return await Task.FromResult<ChatMessageBase>(result).ConfigureAwait(false);
    }

    public async IAsyncEnumerable<ChatMessageBase> GetStreamingChatMessageAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var message = await this.GetChatMessageAsync(cancellationToken).ConfigureAwait(false);

        if (!string.IsNullOrWhiteSpace(message.Content))
        {
            yield return message;
        }
    }

    public async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var result in this.GetStreamingChatMessageAsync(cancellationToken))
        {
            if (!string.IsNullOrWhiteSpace(result.Content))
            {
                yield return result.Content;
            }
        }
    }

    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        var message = await this.GetChatMessageAsync(cancellationToken).ConfigureAwait(false);

        return message.Content;
    }

    #region private ================================================================================

    private readonly ChatWithDataStreamingChoice _choice;

    private bool IsValidMessage(ChatWithDataStreamingMessage message)
    {
        return !message.EndTurn &&
            (message.Delta.Role is null || !message.Delta.Role.Equals(AuthorRole.Tool.Label, StringComparison.Ordinal));
    }

    private string? GetToolContent(ChatWithDataStreamingChoice choice)
    {
        var message = choice.Messages
            .FirstOrDefault(message => message.Delta.Role is not null && message.Delta.Role.Equals(AuthorRole.Tool.Label, StringComparison.Ordinal));

        return message?.Delta?.Content;
    }

    #endregion
}

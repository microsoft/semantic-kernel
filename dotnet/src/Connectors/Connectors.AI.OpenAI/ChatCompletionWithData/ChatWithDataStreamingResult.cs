// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

internal sealed class ChatWithDataStreamingResult : IChatStreamingResult
{
    public ChatWithDataStreamingResult(ChatWithDataStreamingChoice choice)
    {
        Verify.NotNull(choice);

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
        yield return await this.GetChatMessageAsync(cancellationToken).ConfigureAwait(false);
    }

    #region private ================================================================================

    private readonly ChatWithDataStreamingChoice _choice;

    private bool IsValidMessage(ChatWithDataStreamingMessage message)
    {
        return !message.EndTurn &&
            (message.Delta.Role is null || !message.Delta.Role.Equals(AuthorRole.Tool.Label, StringComparison.Ordinal));
    }

    #endregion
}

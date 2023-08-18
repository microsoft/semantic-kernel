// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

internal sealed class ChatWithDataResult : IChatResult
{
    public ChatWithDataResult(ChatWithDataChoice choice)
    {
        Verify.NotNull(choice);

        this._choice = choice;
    }

    public Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
    {
        var message = this._choice.Messages
            .FirstOrDefault(message => message.Role.Equals(AuthorRole.Assistant.Label, StringComparison.Ordinal));

        return Task.FromResult<ChatMessageBase>(new SKChatMessage(message.Role, message.Content));
    }

    #region private ================================================================================

    private readonly ChatWithDataChoice _choice;

    #endregion
}

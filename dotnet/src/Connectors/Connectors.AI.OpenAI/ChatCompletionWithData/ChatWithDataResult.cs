// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

internal sealed class ChatWithDataResult : IChatResult, ITextResult
{
    public ModelResult ModelResult { get; }

    public ChatWithDataResult(ChatWithDataResponse response, ChatWithDataChoice choice)
    {
        Verify.NotNull(response);
        Verify.NotNull(choice);

        this.ModelResult = new(new ChatWithDataModelResult(response.Id, DateTimeOffset.FromUnixTimeSeconds(response.Created)));

        this._choice = choice;
    }

    public Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
    {
        var message = this._choice.Messages
            .FirstOrDefault(message => message.Role.Equals(AuthorRole.Assistant.Label, StringComparison.Ordinal));

        return Task.FromResult<ChatMessageBase>(new SKChatMessage(message.Role, message.Content));
    }

    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        var message = await this.GetChatMessageAsync(cancellationToken).ConfigureAwait(false);

        return message.Content;
    }

    #region private ================================================================================

    private readonly ChatWithDataChoice _choice;

    #endregion
}

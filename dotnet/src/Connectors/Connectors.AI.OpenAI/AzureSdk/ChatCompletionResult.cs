// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal sealed class ChatResult : IChatResult, ITextCompletionResult
{
    private readonly ChatChoice _choice;

    public ChatResult(ChatChoice choice)
    {
        Verify.NotNull(choice);
        this._choice = choice;
    }

    public Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
        => Task.FromResult<ChatMessageBase>(new SKChatMessage(this._choice.Message));

    public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._choice.Message.Content);
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal sealed class ChatCompletionResult : IChatCompletionResult
{
    private readonly ChatChoice _choice;

    public ChatCompletionResult(ChatChoice choice)
    {
        this._choice = choice;
    }

    public async Task<IChatMessage> GetChatMessageAsync(CancellationToken cancellationToken = default)
    {
        return await Task.FromResult(new ChatMessageAdapter(this._choice.Message)).ConfigureAwait(false);
    }
}

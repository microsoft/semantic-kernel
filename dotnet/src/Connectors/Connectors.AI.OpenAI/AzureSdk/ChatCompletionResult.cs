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
        return await Task.FromResult(new ChatMessage(this._choice.Message)).ConfigureAwait(false);
    }
}

public class ChatMessage : IChatMessage
{
    private readonly Azure.AI.OpenAI.ChatMessage _message;

    public ChatMessage(Azure.AI.OpenAI.ChatMessage message)
    {
        this._message = message;
    }

    public string Role => this._message.Role.ToString();
    public string Content => this._message.Content;
}

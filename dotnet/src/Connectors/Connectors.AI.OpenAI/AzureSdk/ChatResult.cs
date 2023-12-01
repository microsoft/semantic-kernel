// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal sealed class ChatResult : IChatResult, ITextResult
{
    private readonly ChatChoice _choice;

    public ChatResult(ChatCompletions resultData, ChatChoice choice)
    {
        Verify.NotNull(choice);
        this._choice = choice;
        this.ModelResult = new(new ChatModelResult(resultData, choice));
    }

    public ModelResult ModelResult { get; }

    public Task<SemanticKernel.AI.ChatCompletion.ChatMessage> GetChatMessageAsync(CancellationToken cancellationToken = default)
        => Task.FromResult<SemanticKernel.AI.ChatCompletion.ChatMessage>(new AzureOpenAIChatMessage(this._choice.Message));

    public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._choice.Message.Content);
    }
}

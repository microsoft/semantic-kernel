// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal sealed class ChatResult : IChatResult, ITextCompletionResult
{
    private readonly ModelResult _modelResult;
    private readonly ChatChoice _choice;

    public ChatResult(ChatCompletions resultData, ChatChoice choice)
    {
        Verify.NotNull(choice);
        this._choice = choice;
        this._modelResult = new ModelResult(resultData);
    }

    public ModelResult ModelResult => this._modelResult;

    public Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
        => Task.FromResult<ChatMessageBase>(new SKChatMessage(this._choice.Message));

    public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._choice.Message.Content);
    }
}

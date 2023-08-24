// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.ChatCompletion;

/// <summary>
/// Oobabooga implementation of <see cref="IChatResult"/>. Actual response object is stored in a ModelResult instance, and completion text is simply passed forward.
/// </summary>
internal sealed class ChatCompletionResult : IChatResult
{
    private readonly ModelResult _responseData;

    public ChatCompletionResult(ChatCompletionResponseHistory responseData)
    {
        this._responseData = new ModelResult(responseData);
    }

    public ModelResult ModelResult => this._responseData;

    public Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult((ChatMessageBase)new SKChatMessage(this._responseData.GetResult<ChatCompletionResponseHistory>().History.Visible.Last()));
    }
}

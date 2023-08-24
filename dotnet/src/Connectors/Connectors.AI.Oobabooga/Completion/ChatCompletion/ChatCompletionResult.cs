// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.ChatCompletion;

/// <summary>
/// Oobabooga implementation of <see cref="IChatResult"/> and <see cref="ITextResult"/>. Actual response object is stored in a ModelResult instance, and completion text is simply passed forward.
/// </summary>
internal sealed class ChatCompletionResult : IChatResult, ITextResult
{
    public ChatCompletionResult(ChatCompletionResponseHistory responseData)
    {
        this._responseHistory = responseData;
        this.ModelResult = new ModelResult(responseData);
    }

    public ModelResult ModelResult { get; }

    public Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult((ChatMessageBase)new SKChatMessage(this._responseHistory.History.Visible.Last()));
    }

    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        var message = await this.GetChatMessageAsync(cancellationToken).ConfigureAwait(false);

        return message.Content;
    }

    #region private ================================================================================

    private readonly ChatCompletionResponseHistory _responseHistory;

    #endregion
}

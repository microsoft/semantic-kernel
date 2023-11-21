// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.Anthropic;

internal sealed class ChatResult : IChatResult, IChatStreamingResult, ITextResult, ITextStreamingResult
{
    private readonly AnthropicResponse _response;

    internal ChatResult(AnthropicResponse response)
    {
        this._response = response;
    }

    /// <inheritdoc/>
    public ModelResult ModelResult => new(this._response.Completion);

    /// <inheritdoc/>
    public Task<ChatMessage> GetChatMessageAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(new ChatMessage(AuthorRole.Assistant, this._response.Completion));
    }

    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        var message = await this.GetChatMessageAsync(cancellationToken).ConfigureAwait(false);
        return message.Content;
    }

    public async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var message in this.GetStreamingChatMessageAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return message.Content;
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<ChatMessage> GetStreamingChatMessageAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var _messages = new[] { new ChatMessage(AuthorRole.Assistant, this._response.Completion) };
        foreach (var _message in _messages)
        {
            await Task.Yield();
            yield return _message;
        }
    }
}

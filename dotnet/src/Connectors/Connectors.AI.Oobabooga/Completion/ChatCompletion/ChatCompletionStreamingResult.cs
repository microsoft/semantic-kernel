// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.ChatCompletion;

internal sealed class ChatCompletionStreamingResult : CompletionStreamingResultBase, IChatStreamingResult
{
    private readonly Channel<ChatMessageBase> _chatMessageChannel;

    public ChatCompletionStreamingResult()
    {
        this._chatMessageChannel = Channel.CreateUnbounded<ChatMessageBase>(new UnboundedChannelOptions()
        {
            SingleReader = true,
            SingleWriter = true,
            AllowSynchronousContinuations = false
        });
    }

    public void AppendResponse(ChatCompletionStreamingResponse response)
    {
        this.ModelResponses.Add(response);
        if (response.History.Visible.Count > 0)
        {
            this._chatMessageChannel.Writer.TryWrite(new SKChatMessage(response.History.Visible));
        }
    }

    public override void AppendResponse(CompletionStreamingResponseBase response)
    {
        this.AppendResponse((ChatCompletionStreamingResponse)response);
    }

    public override void SignalStreamEnd()
    {
        this._chatMessageChannel.Writer.Complete();
    }

    public async Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
    {
        return await this._chatMessageChannel.Reader.ReadAsync(cancellationToken).ConfigureAwait(false);
    }

    public async IAsyncEnumerable<ChatMessageBase> GetStreamingChatMessageAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        while (await this._chatMessageChannel.Reader.WaitToReadAsync(cancellationToken).ConfigureAwait(false))
        {
            while (this._chatMessageChannel.Reader.TryRead(out ChatMessageBase? chunk))
            {
                yield return chunk;
            }
        }
    }
}

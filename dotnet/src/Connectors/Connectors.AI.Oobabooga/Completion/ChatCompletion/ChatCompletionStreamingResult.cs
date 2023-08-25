// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.ChatCompletion;

public sealed class ChatCompletionStreamingResult : CompletionStreamingResultBase, IChatStreamingResult, ITextStreamingResult
{
    private readonly Channel<ChatMessageBase> _chatMessageChannel = Channel.CreateUnbounded<ChatMessageBase>(new UnboundedChannelOptions()
    {
        SingleReader = true,
        SingleWriter = true,
        AllowSynchronousContinuations = false
    });

    private void AppendResponse(ChatCompletionStreamingResponse response)
    {
        this.ModelResponses.Add(response);
        if (response.History.Visible.Count > 0)
        {
            this._chatMessageChannel.Writer.TryWrite(new SKChatMessage(response.History.Visible.Last()));
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

    public async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var result in this.GetStreamingChatMessageAsync(cancellationToken))
        {
            yield return result.Content;
        }
    }

    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        var message = await this.GetChatMessageAsync(cancellationToken).ConfigureAwait(false);

        return message.Content;
    }
}

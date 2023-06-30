// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Channels;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion.TextCompletionResults;

/// <summary>
/// Single use Oobabooga implementation of <see cref="ITextAsyncStreamingResult"/>. Actual response object are stored in a ModelResult instance, and completion text is simply passed forward. This implementation is meant for single consumer, and result content can only be enumerated once even though the entire sequence is stored in ModelResult property .
/// </summary>
internal sealed class ChannelBasedTextCompletionStreamingResult : TextCompletionStreamingResultBase
{
    private readonly Channel<string> _responseChannel;

    public ChannelBasedTextCompletionStreamingResult() : base()
    {
        this._responseChannel = Channel.CreateUnbounded<string>(new UnboundedChannelOptions()
        {
            SingleReader = true,
            SingleWriter = true,
            AllowSynchronousContinuations = true
        });
    }

    public override void AppendResponse(TextCompletionStreamingResponse response)
    {
        this.AppendModelResult(response);
        this._responseChannel.Writer.TryWrite(response.Text);
    }

    public override void SignalStreamEnd()
    {
        this._responseChannel.Writer.Complete();
    }

    public override async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        while (await this._responseChannel.Reader.WaitToReadAsync(cancellationToken).ConfigureAwait(false))
        {
            while (this._responseChannel.Reader.TryRead(out string? chunk))
            {
                yield return chunk;
            }
        }
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks.Dataflow;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion.TextCompletionResults;

/// <summary>
/// BroadcastBlock-based implementation of <see cref="ITextAsyncStreamingResult"/>. This implementation allows the same stream to be consumed by multiple consumers simultaneously. Response object are stored in a ModelResult instance, and completion text is simply passed forward.
/// </summary>
internal sealed class BroadcastBlockBasedTextCompletionStreamingResult : TextCompletionStreamingResultBase
{
    private readonly BroadcastBlock<string> _broadcastBlock;
    private readonly object _syncLock = new();
    private int _lastConsumedPosition = -1;

    public BroadcastBlockBasedTextCompletionStreamingResult() : base()
    {
        this._broadcastBlock = new BroadcastBlock<string>(i => i);
    }

    public override void AppendResponse(TextCompletionStreamingResponse response)
    {
        lock (this._syncLock)
        {
            this.AppendModelResult(response);
            this._broadcastBlock.Post(response.Text);
        }
    }

    public override void SignalStreamEnd()
    {
        this._broadcastBlock.Complete();
    }

    public override async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var targetBlock = new BufferBlock<string>();
        this._broadcastBlock.LinkTo(targetBlock, new DataflowLinkOptions { PropagateCompletion = true });

        // Catching up with existing data.
        lock (this._syncLock)
        {
            for (int i = this._lastConsumedPosition + 1; i < this.ModelResponses.Count; i++)
            {
                yield return this.ModelResponses[i].Text;
            }

            this._lastConsumedPosition = this.ModelResponses.Count - 1;
        }

        // Listening for new data.
        while (await targetBlock.OutputAvailableAsync(cancellationToken).ConfigureAwait(false))
        {
            while (targetBlock.TryReceive(out string? chunk))
            {
                yield return chunk;
            }
        }
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
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

    private bool _isConsuming = false;

    public override async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var targetBlock = new BufferBlock<string>();

        // Temporary list to hold data to be sent to the consumers.
        List<string>? tempList = null;

        // Catching up with existing data.
        lock (this._syncLock)
        {
            if (!this._isConsuming)
            {
                // First consumer doesn't need to catch up, so set the flag
                this._isConsuming = true;
            }
            else
            {
                // Later consumers need to catch up
                tempList = this.ModelResponses.Select(response => response.Text).ToList();
            }

            this._broadcastBlock.LinkTo(targetBlock, new DataflowLinkOptions { PropagateCompletion = true });
        }

        if (tempList != null)
        {
            // Yield the data outside the lock.
            foreach (var item in tempList)
            {
                yield return item;
            }
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

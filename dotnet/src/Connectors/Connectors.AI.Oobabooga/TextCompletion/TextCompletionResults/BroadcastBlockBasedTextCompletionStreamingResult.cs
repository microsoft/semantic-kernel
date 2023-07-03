// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Threading.Tasks.Dataflow;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion.TextCompletionResults;

/// <summary>
/// BroadcastBlock-based implementation of <see cref="ITextAsyncStreamingResult"/>. This implementation allows the same stream to be consumed by multiple consumers simultaneously. Response object are stored in a ModelResult instance, and completion text is simply passed forward.
/// </summary>
internal sealed class BroadcastBlockBasedTextCompletionStreamingResult : ITextAsyncStreamingResult
{
    private readonly ILogger? _logger;
    private readonly BroadcastBlock<string> _broadcastBlock;
    private readonly object _syncLock;
    private bool _isProducing;
    private readonly List<TextCompletionStreamingResponse> _modelResponses;

    public ModelResult ModelResult { get; }

    public BroadcastBlockBasedTextCompletionStreamingResult(ILogger? logger = null) : base()
    {
        this._logger = logger;
        this._isProducing = false;
        this._syncLock = new();
        this._modelResponses = new();
        this.ModelResult = new ModelResult(this._modelResponses);
        this._broadcastBlock = new BroadcastBlock<string>(i => i);
    }

    public void AppendResponse(TextCompletionStreamingResponse response)
    {
        lock (this._syncLock)
        {
            if (!this._isProducing)
            {
                this._logger?.LogTrace(message: $"First producer");
                this._isProducing = true;
            }

            this._logger?.LogTrace(message: $"Adding item {response.Text}");
            this._modelResponses.Add(response);
            this._broadcastBlock.Post(response.Text);
        }
    }

    public void SignalStreamEnd()
    {
        this._logger?.LogTrace(message: $"Completing");
        this._broadcastBlock.Complete();
    }

    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        StringBuilder resultBuilder = new();

        await foreach (var chunk in this.GetCompletionStreamingAsync(cancellationToken))
        {
            resultBuilder.Append(chunk);
        }

        return resultBuilder.ToString();
    }

    public async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var targetBlock = new BufferBlock<string>();

        // Temporary list to hold data to be sent to the consumers.
        List<string>? tempList = null;

        // Catching up with existing data.
        lock (this._syncLock)
        {
            if (!this._isProducing)
            {
                this._logger?.LogTrace(message: $"First consumer");
                // First consumer doesn't need to catch up, so set the flag
                this._isProducing = true;
            }
            else
            {
                this._logger?.LogTrace(message: $"Catching up");
                // Later consumers need to catch up
                tempList = this._modelResponses.Select(response => response.Text).ToList();
            }

            this._broadcastBlock.LinkTo(targetBlock, new DataflowLinkOptions { PropagateCompletion = true });
        }

        if (tempList != null)
        {
            // Yield the data outside the lock.
            foreach (var item in tempList)
            {
                this._logger?.LogTrace(message: $"yielding catchup item {item}");
                yield return item;
            }
        }

        // Listening for new data.
        while (await targetBlock.OutputAvailableAsync(cancellationToken).ConfigureAwait(false))
        {
            while (targetBlock.TryReceive(out string? chunk))
            {
                this._logger?.LogTrace(message: $"yielding broadcast item {chunk}");
                yield return chunk;
            }
        }
    }
}

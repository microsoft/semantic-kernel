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
    private readonly List<TextCompletionStreamingResponse> _modelResponses;
    private bool _completed = false;

    public ModelResult ModelResult { get; }

    public BroadcastBlockBasedTextCompletionStreamingResult(ILogger? logger = null) : base()
    {
        this._logger = logger;
        this._syncLock = new();
        this._modelResponses = new();
        this.ModelResult = new ModelResult(this._modelResponses);
        this._broadcastBlock = new BroadcastBlock<string>(i => i);
    }

    public void AppendResponse(TextCompletionStreamingResponse response)
    {
        lock (this._syncLock)
        {
            this._broadcastBlock.Post(response.Text);
            this._logger?.LogTrace(message: $"Adding item {response.Text}");
            this._modelResponses.Add(response);
        }
    }

    public void SignalStreamEnd()
    {
        this._logger?.LogTrace(message: "Completing broadcast");
        lock (this._syncLock)
        {
            this._broadcastBlock.Complete();
            this._completed = true;
        }
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
        List<string> tempList;
        bool completed;

        BufferBlock<string>? targetBlock = null;

        lock (this._syncLock)
        {
            tempList = this._modelResponses.Select(response => response.Text).ToList();
            completed = this._completed;
            if (!completed)
            {
                targetBlock = new();
                this._broadcastBlock.LinkTo(targetBlock, new DataflowLinkOptions { PropagateCompletion = true });
            }
        }

        foreach (var item in tempList)
        {
            this._logger?.LogTrace(message: $"yielding catch up item {item}");
            yield return item;
        }

        if (!completed)
        {
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
}

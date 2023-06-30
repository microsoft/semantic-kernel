// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion.TextCompletionResults;

/// <summary>
/// Monitor-based implementation of <see cref="ITextAsyncStreamingResult"/>. This implementation can be enumerated by several consumers simultaneously or sequentially. Response object are stored in a ModelResult instance, and completion text is simply passed forward.
/// </summary>
internal sealed class MonitorBasedTextCompletionStreamingResult : TextCompletionStreamingResultBase
{
    private bool _streamEndSignaled;
    private readonly object _syncLock;

    public MonitorBasedTextCompletionStreamingResult() : base()
    {
        this._streamEndSignaled = false;
        this._syncLock = new();
    }

    public override void AppendResponse(TextCompletionStreamingResponse response)
    {
        lock (this._syncLock)
        {
            this.AppendModelResult(response);
            Monitor.PulseAll(this._syncLock);
        }
    }

    public override void SignalStreamEnd()
    {
        lock (this._syncLock)
        {
            this._streamEndSignaled = true;
            Monitor.PulseAll(this._syncLock);
        }
    }

    public override async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var results = await Task.Run(this.GetCompletionResults, cancellationToken).ConfigureAwait(false);
        foreach (var result in results)
        {
            yield return result;
        }
    }

    private IEnumerable<string> GetCompletionResults()
    {
        var index = 0;
        bool hasMoreItems = true;
        while (hasMoreItems)
        {
            TextCompletionStreamingResponse? response = null;
            lock (this._syncLock)
            {
                while (!this._streamEndSignaled && index >= this.ModelResponses.Count)
                {
                    Monitor.Wait(this._syncLock);
                }

                if (index < this.ModelResponses.Count)
                {
                    response = this.ModelResponses[index++];
                }
                else
                {
                    hasMoreItems = !this._streamEndSignaled;
                }
            }

            if (response != null)
            {
                yield return response.Text;
            }
        }
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;

/// <summary>
/// Oobabooga implementation of <see cref="ITextStreamingResult"/>. Actual response object are stored in a ModelResult instance, and completion text is simply passed forward.
/// </summary>
internal sealed class TextCompletionStreamingResult : ITextStreamingResult
{
    private readonly List<TextCompletionStreamingResponse> _modelResponses;
    private bool _streamEndSignaled = false;
    private readonly object _syncLock = new();

    public ModelResult ModelResult { get; }

    public TextCompletionStreamingResult()
    {
        this._modelResponses = new List<TextCompletionStreamingResponse>();
        this.ModelResult = new ModelResult(this._modelResponses);
    }

    public void AppendResponse(TextCompletionStreamingResponse response)
    {
        lock (this._syncLock)
        {
            this._modelResponses.Add(response);
            Monitor.PulseAll(this._syncLock);
        }
    }

    public void SignalStreamEnd()
    {
        lock (this._syncLock)
        {
            this._streamEndSignaled = true;
            Monitor.PulseAll(this._syncLock);
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
        var index = 0;

        while (true)
        {
            lock (this._syncLock)
            {
                while (!this._streamEndSignaled && index >= this._modelResponses.Count)
                {
                    Monitor.Wait(this._syncLock);
                }

                if (index < this._modelResponses.Count)
                {
                    yield return this._modelResponses[index++].Text;
                }
                else
                {
                    yield break;
                }
            }
        }
    }
}

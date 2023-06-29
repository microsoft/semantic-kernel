// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
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
    private readonly ConcurrentQueue<string> _responseChunks;

    private readonly List<TextCompletionStreamingResponse> _modelResponses;
    private readonly SemaphoreSlim _semaphore;

    public ModelResult ModelResult { get; }
    private bool _streamEndSignaled;

    public TextCompletionStreamingResult()
    {
        this._responseChunks = new();
        this._modelResponses = new();
        this.ModelResult = new ModelResult(this._modelResponses);
        this._semaphore = new SemaphoreSlim(0);
    }

    public void AppendResponse(TextCompletionStreamingResponse response)
    {
        this._responseChunks.Enqueue(response.Text);
        this._modelResponses.Add(response);
        this._semaphore.Release();
    }

    public void SignalStreamEnd()
    {
        this._streamEndSignaled = true;
        this._semaphore.Release();
    }

    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        StringBuilder resultBuilder = new();

        await foreach (var chunk in this.GetResponseChunksAsync(cancellationToken))
        {
            resultBuilder.Append(chunk);
        }

        return resultBuilder.ToString();
    }

    public async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var chunk in this.GetResponseChunksAsync(cancellationToken))
        {
            yield return chunk;
        }
    }

    private async IAsyncEnumerable<string> GetResponseChunksAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        while (!cancellationToken.IsCancellationRequested)
        {
            while (this._responseChunks.TryDequeue(out string responseChunk))
            {
                yield return responseChunk;
            }

            if (this._streamEndSignaled)
            {
                yield break;
            }
            else
            {
                await this._semaphore.WaitAsync(cancellationToken).ConfigureAwait(false);
            }
        }
    }
}

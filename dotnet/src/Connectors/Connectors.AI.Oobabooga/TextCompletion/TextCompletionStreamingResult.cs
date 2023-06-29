// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;
using System.Threading.Channels;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion;

/// <summary>
/// Oobabooga implementation of <see cref="ITextStreamingResult"/>. Actual response object are stored in a ModelResult instance, and completion text is simply passed forward.
/// </summary>
internal sealed class TextCompletionStreamingResult : ITextStreamingResult
{
    private readonly Channel<string> _responseChannel;

    private readonly List<TextCompletionStreamingResponse> _modelResponses;
    public ModelResult ModelResult { get; }

    public TextCompletionStreamingResult()
    {
        this._responseChannel = Channel.CreateUnbounded<string>(new UnboundedChannelOptions()
        {
            SingleReader = true,
            SingleWriter = true,
            AllowSynchronousContinuations = true
        });
        this._modelResponses = new();
        this.ModelResult = new ModelResult(this._modelResponses);
    }

    public void AppendResponse(TextCompletionStreamingResponse response)
    {
        this._responseChannel.Writer.TryWrite(response.Text);
        this._modelResponses.Add(response);
    }

    public void SignalStreamEnd()
    {
        this._responseChannel.Writer.Complete();
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
        while (await this._responseChannel.Reader.WaitToReadAsync(cancellationToken).ConfigureAwait(false))
        {
            while (this._responseChannel.Reader.TryRead(out string? chunk))
            {
                yield return chunk;
            }
        }
    }
}

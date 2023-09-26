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

internal sealed class TextCompletionStreamingResult : ITextStreamingResult
{
    private readonly List<TextCompletionStreamingResponse> _modelResponses;
    private readonly Channel<string> _responseChannel;

    public ModelResult ModelResult { get; }

    public TextCompletionStreamingResult()
    {
        this._modelResponses = new();
        this.ModelResult = new ModelResult(this._modelResponses);
        this._responseChannel = Channel.CreateUnbounded<string>(new UnboundedChannelOptions()
        {
            SingleReader = true,
            SingleWriter = true,
            AllowSynchronousContinuations = false
        });
    }

    public void AppendResponse(TextCompletionStreamingResponse response)
    {
        this._modelResponses.Add(response);
        this._responseChannel.Writer.TryWrite(response.Text);
    }

    public void SignalStreamEnd()
    {
        this._responseChannel.Writer.Complete();
    }

    public async Task<string> GetTextAsync(CancellationToken cancellationToken = default)
    {
        StringBuilder resultBuilder = new();

        await foreach (var chunk in this.GetTextStreamingAsync(cancellationToken))
        {
            resultBuilder.Append(chunk);
        }

        return resultBuilder.ToString();
    }

    public async IAsyncEnumerable<string> GetTextStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
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

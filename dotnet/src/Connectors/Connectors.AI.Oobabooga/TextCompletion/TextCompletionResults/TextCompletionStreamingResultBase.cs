// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.TextCompletion.TextCompletionResults;

internal abstract class TextCompletionStreamingResultBase : ITextAsyncStreamingResult
{
    protected readonly List<TextCompletionStreamingResponse> ModelResponses;

    public ModelResult ModelResult { get; }

    protected TextCompletionStreamingResultBase()
    {
        this.ModelResponses = new();
        this.ModelResult = new ModelResult(this.ModelResponses);
    }

    protected void AppendModelResult(TextCompletionStreamingResponse response)
    {
        this.ModelResponses.Add(response);
    }

    public abstract void AppendResponse(TextCompletionStreamingResponse response);

    public abstract void SignalStreamEnd();

    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        StringBuilder resultBuilder = new();

        await foreach (var chunk in this.GetCompletionStreamingAsync(cancellationToken))
        {
            resultBuilder.Append(chunk);
        }

        return resultBuilder.ToString();
    }

    public abstract IAsyncEnumerable<string> GetCompletionStreamingAsync(CancellationToken cancellationToken = default);
}

// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal sealed class TextStreamingResult : ITextStreamingResult, ITextResult
{
    public ModelResult ModelResult { get; }

    public TextStreamingResult(Completions completions, IReadOnlyList<Choice> choices)
    {
        this.ModelResult = new ModelResult(completions);
        this._choices = choices;
    }

    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        var fullMessage = new StringBuilder();
        await foreach (var message in this.GetCompletionStreamingAsync(cancellationToken).ConfigureAwait(false))
        {
            fullMessage.Append(message);
        }

        return fullMessage.ToString();
    }

    public async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        int currentIndex = -1;
        while (currentIndex < this._choices.Count)
        {
            currentIndex++;

            yield return this._choices[currentIndex].Text;

            // Wait for next choice update...
            while (!this._isStreamEnded && currentIndex >= this._choices.Count)
            {
                await Task.Delay(50, cancellationToken).ConfigureAwait(false);
            }
        }
    }

    private readonly IReadOnlyList<Choice> _choices;
    private bool _isStreamEnded = false;

    internal void EndOfStream()
    {
        this._isStreamEnded = true;
    }
}

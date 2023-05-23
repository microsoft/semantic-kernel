// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal sealed class TextCompletionResult : ITextCompletionResult
{
    private readonly Completions _resultData;
    private readonly Choice _choice;

    public TextCompletionResult(Completions resultData, Choice choice)
    {
        this._resultData = resultData;
        this._choice = choice;
    }

    public object? ResultData => this._resultData;

    public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._choice.Text);
    }

    public Task<Completions> GetResultDetailsAsync()
    {
        return Task.FromResult(this._resultData);
    }
}

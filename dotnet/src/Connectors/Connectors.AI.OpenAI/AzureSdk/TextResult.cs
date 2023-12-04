// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI;

internal sealed class TextResult : ITextResult
{
    private readonly ModelResult _modelResult;
    private readonly Choice _choice;

    public TextResult(Completions resultData, Choice choice)
    {
        this._modelResult = new(new TextModelResult(resultData, choice));
        this._choice = choice;
    }

    public ModelResult ModelResult => this._modelResult;

    public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this._choice.Text);
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI.TextCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal class TextCompletionResultBase : ITextCompletionResult
{
    private readonly Choice _choice;

    public TextCompletionResultBase(Choice choice)
    {
        this._choice = choice;
    }

    public async Task<string> CompleteAsync(CancellationToken cancellationToken = default)
    {
        return this._choice.Text;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace SemanticKernel.Connectors.UnitTests.MultiConnector.TextCompletion.ArithmeticMocks;

public abstract class ArithmeticStreamingResultBase : ITextStreamingResult
{
    private ModelResult? _modelResult;

    public ModelResult ModelResult => this._modelResult ?? this.GenerateModelResult().Result;

    protected abstract Task<ModelResult> GenerateModelResult();

    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        this._modelResult = await this.GenerateModelResult();
        return this.ModelResult?.GetResult<string>() ?? string.Empty;
    }

    public async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        this._modelResult = await this.GenerateModelResult();

        string resultText = this.ModelResult.GetResult<string>();
        // Your model logic here
        var streamedOutput = resultText.Split(' ');
        foreach (string word in streamedOutput)
        {
            yield return $"{word} ";
        }
    }
}

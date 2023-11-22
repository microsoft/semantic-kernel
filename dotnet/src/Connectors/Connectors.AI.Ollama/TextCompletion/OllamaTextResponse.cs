// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.Ollama.TextCompletion;

internal sealed class OllamaTextResponse : ITextResult
{
    public ModelResult ModelResult { get; }

    public OllamaTextResponse(ModelResult modelResult)
    {
        this.ModelResult = modelResult;
    }

    public Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        return Task.FromResult(this.ModelResult.GetResult<string>());
    }
}

internal sealed class OllamaTextStreamingResponse : ITextStreamingResult
{
    public ModelResult ModelResult { get; }

    public OllamaTextStreamingResponse(ModelResult modelResult)
    {
        this.ModelResult = modelResult;
    }

    public async IAsyncEnumerable<string> GetCompletionStreamingAsync(CancellationToken cancellationToken = default)
    {
        yield return this.ModelResult.GetResult<string>();
    }
}

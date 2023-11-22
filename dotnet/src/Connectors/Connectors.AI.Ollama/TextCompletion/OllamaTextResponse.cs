using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Connectors.AI.Ollama.TextCompletion;

internal class OllamaTextResponse : ITextResult
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

internal class OllamaTextStreamingResponse : ITextStreamingResult
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

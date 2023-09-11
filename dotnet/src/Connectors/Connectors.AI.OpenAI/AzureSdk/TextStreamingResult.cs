// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal sealed class TextStreamingResult : ITextStreamingResult
{
    private readonly Azure.AI.OpenAI.StreamingChoice _choice;

    public ModelResult ModelResult { get; }

    public TextStreamingResult(StreamingCompletions resultData, Azure.AI.OpenAI.StreamingChoice choice)
    {
        this.ModelResult = new ModelResult(resultData);
        this._choice = choice;
    }

    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        var fullMessage = new StringBuilder();
        await foreach (var message in this._choice.GetTextStreaming(cancellationToken).ConfigureAwait(false))
        {
            fullMessage.Append(message);
        }

        return fullMessage.ToString();
    }

    public IAsyncEnumerable<string> GetCompletionStreamingAsync(CancellationToken cancellationToken = default)
    {
        return this._choice.GetTextStreaming(cancellationToken);
    }

    public Task<Stream> GetRawStreamAsync(CancellationToken cancellationToken = default)
    {
        var memoryStream = new MemoryStream();

        _ = Task.Run(async () =>
        {
            using var streamWriter = new StreamWriter(memoryStream);
            await foreach (var content in this._choice.GetTextStreaming(cancellationToken).ConfigureAwait(false))
            {
                await streamWriter.WriteAsync(content).ConfigureAwait(false);
            }
            await streamWriter.FlushAsync().ConfigureAwait(false);
            streamWriter.Close();
        }, cancellationToken);

        return Task.FromResult<Stream>(memoryStream);
    }
}

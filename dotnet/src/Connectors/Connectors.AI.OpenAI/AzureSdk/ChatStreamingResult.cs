// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal sealed class ChatStreamingResult : IChatStreamingResult, ITextStreamingResult
{
    private readonly ModelResult _modelResult;
    private readonly StreamingChatChoice _choice;

    public ChatStreamingResult(StreamingChatCompletions resultData, StreamingChatChoice choice)
    {
        Verify.NotNull(choice);
        this._modelResult = new ModelResult(resultData);
        this._choice = choice;
    }

    public ModelResult ModelResult => this._modelResult;

    /// <inheritdoc/>
    public async Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
    {
        var chatMessage = await this._choice.GetMessageStreaming(cancellationToken)
                                                .LastOrDefaultAsync(cancellationToken)
                                                .ConfigureAwait(false);

        if (chatMessage is null)
        {
            throw new SKException("Unable to get chat message from stream");
        }

        return new SKChatMessage(chatMessage);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<ChatMessageBase> GetStreamingChatMessageAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var message in this._choice.GetMessageStreaming(cancellationToken))
        {
            yield return new SKChatMessage(message);
        }
    }

    /// <inheritdoc/>
    public async Task<string> GetCompletionAsync(CancellationToken cancellationToken = default)
    {
        return (await this.GetChatMessageAsync(cancellationToken).ConfigureAwait(false)).Content;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCompletionStreamingAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        await foreach (var result in this.GetStreamingChatMessageAsync(cancellationToken).ConfigureAwait(false))
        {
            yield return result.Content;
        }
    }

    public Task<Stream> GetRawStreamAsync(CancellationToken cancellationToken = default)
    {
        var memoryStream = new MemoryStream();

        _ = Task.Run(async () =>
        {
            using var streamWriter = new StreamWriter(memoryStream);
            await foreach (var result in this.GetStreamingChatMessageAsync(cancellationToken).ConfigureAwait(false))
            {
                await streamWriter.WriteAsync(result.Content).ConfigureAwait(false);
            }
            await streamWriter.FlushAsync().ConfigureAwait(false);
            streamWriter.Close();
        }, cancellationToken);

        return Task.FromResult<Stream>(memoryStream);
    }
}

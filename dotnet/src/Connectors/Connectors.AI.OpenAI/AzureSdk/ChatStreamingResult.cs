// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

internal sealed class ChatStreamingResult : IChatStreamingResult, ITextStreamingResult, IChatResult, ITextResult
{
    public ModelResult ModelResult { get; private set; }

    public ChatStreamingResult(IReadOnlyList<StreamingChatCompletionsUpdate> chatUpdates)
    {
        Verify.NotNull(chatUpdates);
        this.ModelResult = new(chatUpdates);
        this._chatUpdates = chatUpdates;
    }

    /// <inheritdoc/>
    public async Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default)
    {
        var fullMessage = new StringBuilder();
        var role = string.Empty;

        await foreach (var message in this.GetStreamingChatMessageAsync(cancellationToken))
        {
            if (string.IsNullOrEmpty(role))
            {
                role = message.Role.ToString();
            }

            fullMessage.Append(message.Content);
        }

        if (fullMessage.Length == 0)
        {
            throw new SKException("Unable to get chat message from stream");
        }

        return new SKChatMessage(role, fullMessage.ToString());
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<ChatMessageBase> GetStreamingChatMessageAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        string role = string.Empty;
        int currentIndex = -1;
        CompletionsFinishReason? finishReason = null;
        string? messageId = null;
        DateTimeOffset? created = null;

        while (currentIndex < this._chatUpdates.Count)
        {
            currentIndex++;

            var message = this._chatUpdates[currentIndex];

            if (message.Role.HasValue)
            {
                role = message.Role.Value.ToString();
            }

            if (message.FinishReason.HasValue)
            {
                finishReason = message.FinishReason.Value;
            }

            if (!string.IsNullOrEmpty(message.Id))
            {
                messageId = message.Id;
            }

            if (message.Created != default)
            {
                created = message.Created;
            }

            if (message.ContentUpdate is { Length: > 0 })
            {
                yield return new SKChatMessage(role, message.ContentUpdate);
            }

            // This part may change to expose the function name and arguments as new properties of a message (not mix with the actual content)
            // FunctionName and FunctionArgumentsUpdate are considered as valid messages
            if (message.FunctionName.Length > 0)
            {
                yield return new SKChatMessage(role, message.FunctionName);
            }

            if (message.FunctionArgumentsUpdate is { Length: > 0 })
            {
                yield return new SKChatMessage(role, message.FunctionArgumentsUpdate);
            }

            // Wait for next choice update...
            while (!this._isStreamEnded && currentIndex >= this._chatUpdates.Count)
            {
                await Task.Delay(50, cancellationToken).ConfigureAwait(false);
            }
        }

        // In the end of the stream is supposed to have all the information to create a ModelResult
        this.ModelResult = new(new ChatStreamingModelResult(finishReason!.Value, messageId!, created!.Value));
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
            if (result.Content is string content and { Length: > 0 })
            {
                yield return content;
            }
        }
    }

    private readonly IReadOnlyList<StreamingChatCompletionsUpdate> _chatUpdates;
    private bool _isStreamEnded = false;

    internal void EndOfStream()
    {
        this._isStreamEnded = true;
    }
}

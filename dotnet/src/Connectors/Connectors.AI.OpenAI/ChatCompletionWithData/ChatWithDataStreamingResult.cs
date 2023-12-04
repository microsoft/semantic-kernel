// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

[Experimental("SKEXP0010")]
internal sealed class ChatWithDataStreamingResult
{
    public ModelResult ModelResult { get; }

    public ChatWithDataStreamingResult(ChatWithDataStreamingResponse response, ChatWithDataStreamingChoice choice)
    {
        Verify.NotNull(response);
        Verify.NotNull(choice);

        this.ModelResult = new(new ChatWithDataModelResult(response.Id, DateTimeOffset.FromUnixTimeSeconds(response.Created))
        {
            ToolContent = this.GetToolContent(choice)
        });

        this._choice = choice;
    }

#pragma warning disable CS1998 // Async method lacks 'await' operators and will run synchronously
    public async IAsyncEnumerable<ChatMessage> GetStreamingChatMessageAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
#pragma warning restore CS1998
    {
        var message = this.GetChatMessage(cancellationToken);

        if (message.Content is { Length: > 0 })
        {
            yield return message;
        }
    }

    #region private ================================================================================
    private AzureOpenAIChatMessage GetChatMessage(CancellationToken cancellationToken = default)
    {
        var message = this._choice.Messages.FirstOrDefault(this.IsValidMessage);

        return new AzureOpenAIChatMessage(AuthorRole.Assistant.Label, message?.Delta?.Content ?? string.Empty);
    }

    private readonly ChatWithDataStreamingChoice _choice;

    private bool IsValidMessage(ChatWithDataStreamingMessage message)
    {
        return !message.EndTurn &&
            (message.Delta.Role is null || !message.Delta.Role.Equals(AuthorRole.Tool.Label, StringComparison.Ordinal));
    }

    private string? GetToolContent(ChatWithDataStreamingChoice choice)
    {
        var message = choice.Messages
            .FirstOrDefault(message => message.Delta.Role is not null && message.Delta.Role.Equals(AuthorRole.Tool.Label, StringComparison.Ordinal));

        return message?.Delta?.Content;
    }

    #endregion
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI;

/// <summary>
/// Streaming chat result update.
/// </summary>
[Experimental("SKEXP0010")]
public sealed class AzureOpenAIWithDataStreamingChatContent : StreamingChatContent
{
    /// <inheritdoc/>
    public string? FunctionName { get; set; }

    /// <inheritdoc/>
    public string? FunctionArgument { get; set; }

    /// <summary>
    /// Create a new instance of the <see cref="OpenAIStreamingChatContent"/> class.
    /// </summary>
    /// <param name="choice">Azure message update representation from WithData apis</param>
    /// <param name="choiceIndex">Index of the choice</param>
    /// <param name="metadata">Additional metadata</param>
    internal AzureOpenAIWithDataStreamingChatContent(ChatWithDataStreamingChoice choice, int choiceIndex, IReadOnlyDictionary<string, object?>? metadata = null) : base(AuthorRole.Assistant, null, choice, choiceIndex, Encoding.UTF8, metadata)
    {
        var message = choice.Messages.FirstOrDefault(this.IsValidMessage);
        var messageContent = message?.Delta?.Content;

        this.Content = messageContent;
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray() => this.Encoding.GetBytes(this.ToString());

    /// <inheritdoc/>
    public override string ToString() => this.Content ?? string.Empty;

    private bool IsValidMessage(ChatWithDataStreamingMessage message)
    {
        return !message.EndTurn &&
            (message.Delta.Role is null || !message.Delta.Role.Equals(AuthorRole.Tool.Label, StringComparison.Ordinal));
    }
}

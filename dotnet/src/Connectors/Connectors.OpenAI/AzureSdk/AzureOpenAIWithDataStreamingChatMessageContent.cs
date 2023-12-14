// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Azure Open AI WithData Specialized streaming chat message content.
/// </summary>
/// <remarks>
/// Represents a chat message content chunk that was streamed from the remote model.
/// </remarks>
[Experimental("SKEXP0010")]
public sealed class AzureOpenAIWithDataStreamingChatMessageContent : StreamingChatMessageContent
{
    /// <inheritdoc/>
    public string? FunctionName { get; set; }

    /// <inheritdoc/>
    public string? FunctionArgument { get; set; }

    /// <summary>
    /// Create a new instance of the <see cref="OpenAIStreamingChatMessageContent"/> class.
    /// </summary>
    /// <param name="choice">Azure message update representation from WithData apis</param>
    /// <param name="choiceIndex">Index of the choice</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    internal AzureOpenAIWithDataStreamingChatMessageContent(ChatWithDataStreamingChoice choice, int choiceIndex, string modelId, IDictionary<string, object?>? metadata = null) : base(AuthorRole.Assistant, null, choice, choiceIndex, modelId, Encoding.UTF8, metadata)
    {
        var message = choice.Messages.FirstOrDefault(this.IsValidMessage);
        var messageContent = message?.Delta?.Content;

        this.Content = messageContent;
    }

    private bool IsValidMessage(ChatWithDataStreamingMessage message)
    {
        return !message.EndTurn &&
            (message.Delta.Role is null || !message.Delta.Role.Equals(AuthorRole.Tool.Label, StringComparison.Ordinal));
    }
}

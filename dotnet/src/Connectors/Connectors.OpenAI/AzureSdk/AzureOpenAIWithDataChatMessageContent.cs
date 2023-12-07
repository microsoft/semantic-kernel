// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// OpenAI specialized with data chat message content
/// </summary>
[Experimental("SKEXP0010")]
public sealed class AzureOpenAIWithDataChatMessageContent : ChatMessageContent
{
    /// <summary>
    /// Content from data source, including citations.
    /// For more information see <see href="https://learn.microsoft.com/en-us/azure/ai-services/openai/concepts/use-your-data#conversation-history-for-better-results"/>.
    /// </summary>
    public string? ToolContent { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIChatMessageContent"/> class.
    /// </summary>
    /// <param name="chatChoice">Azure Chat With Data Choice</param>
    /// <param name="modelId">The model ID used to generate the content</param>
    /// <param name="metadata">Additional metadata</param>
    internal AzureOpenAIWithDataChatMessageContent(ChatWithDataChoice chatChoice, string? modelId, IDictionary<string, object?>? metadata = null)
        : base(default, string.Empty, modelId, chatChoice, System.Text.Encoding.UTF8, metadata ?? new Dictionary<string, object?>(1))
    {
        // An assistant message content must be present, otherwise the chat is not valid.
        var chatMessage = chatChoice.Messages.First(m => string.Equals(m.Role, AuthorRole.Assistant.Label, StringComparison.OrdinalIgnoreCase));

        this.Content = chatMessage.Content;
        this.Role = new AuthorRole(chatMessage.Role);

        this.ToolContent = chatChoice.Messages.FirstOrDefault(message => message.Role.Equals(AuthorRole.Tool.Label, StringComparison.OrdinalIgnoreCase))?.Content;
        this.Metadata!.Add(nameof(this.ToolContent), this.ToolContent);
    }
}

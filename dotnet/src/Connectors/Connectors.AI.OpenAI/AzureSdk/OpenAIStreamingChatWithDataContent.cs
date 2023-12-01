// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Text.Json;
using Microsoft.SemanticKernel.AI.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.AzureSdk;

/// <summary>
/// Streaming chat result update.
/// </summary>
public sealed class OpenAIStreamingChatWithDataContent : StreamingChatContent
{
    /// <summary>
    /// Chat message abstraction
    /// </summary>
    public ChatMessage ChatMessage { get; }

    /// <inheritdoc/>
    public override string? FunctionName { get; protected set; }

    /// <inheritdoc/>
    public override string? FunctionArgument { get; protected set; }

    /// <inheritdoc/>
    public override string? Content { get; protected set; }

    /// <inheritdoc/>
    public override AuthorRole? Role { get; protected set; }

    /// <summary>
    /// Create a new instance of the <see cref="OpenAIStreamingChatContent"/> class.
    /// </summary>
    /// <param name="choice">Azure message update representation from WithData apis</param>
    /// <param name="choiceIndex">Index of the choice</param>
    /// <param name="metadata">Additional metadata</param>
    internal OpenAIStreamingChatWithDataContent(ChatWithDataStreamingChoice choice, int choiceIndex, Dictionary<string, object> metadata) : base(choice, choiceIndex, metadata)
    {
        var message = choice.Messages.FirstOrDefault(this.IsValidMessage);

        this.ChatMessage = new AzureOpenAIChatMessage(AuthorRole.Assistant.Label, message?.Delta?.Content ?? string.Empty);
        this.Content = this.ChatMessage.Content;
        this.Role = this.ChatMessage.Role;
        this.FunctionName = choice.Messages[choiceIndex].Delta.Content ?? string.Empty;
    }

    /// <inheritdoc/>
    public override byte[] ToByteArray()
    {
        return Encoding.UTF8.GetBytes(this.ToString());
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return JsonSerializer.Serialize(this);
    }

    private bool IsValidMessage(ChatWithDataStreamingMessage message)
    {
        return !message.EndTurn &&
            (message.Delta.Role is null || !message.Delta.Role.Equals(AuthorRole.Tool.Label, StringComparison.Ordinal));
    }
}

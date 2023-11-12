// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.AI.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Represents a message that is part of an assistant thread.
/// </summary>
public class ChatMessage
{
    /// <summary>
    /// The id of the assistant associated with the a message where role = "assistant", otherwise null.
    /// </summary>
    public string? AssistantId { get; set; }

    /// <summary>
    /// The role associated with the chat message.
    /// </summary>
    public string Role { get; set; }

    /// <summary>
    /// The chat message content.
    /// </summary>
    public string Content { get; set; }

    /// <summary>
    /// Properties associated with the message.
    /// </summary>
    public Dictionary<string, object>? Properties { get; set; }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="message"></param>
    /// <returns></returns>
    public static ChatMessage CreateUserMessage(string message)
    {
        return
            new ChatMessage(
                type: "text", // $$$ CONST
                message);
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="fileId"></param>
    /// <returns></returns>
    public static ChatMessage CreateUserFile(string fileId)
    {
        return
            new ChatMessage(
                type: "image_file", // $$$ CONST
                fileId);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatMessage"/> class.
    /// </summary>
    /// <param name="type"></param>
    /// <param name="content">$$$</param>
    /// <param name="assistantId"></param>
    /// <param name="properties"></param>
    internal ChatMessage(
        string type,
        string content,
        string? assistantId = null,
        Dictionary<string, object>? properties = null)
    {
        this.AssistantId = string.IsNullOrWhiteSpace(assistantId) ? null : assistantId;
        this.Role = string.IsNullOrWhiteSpace(assistantId) ? AuthorRole.User.Label : AuthorRole.Assistant.Label;
        this.Content = content;
        this.Properties = properties;
    }
}

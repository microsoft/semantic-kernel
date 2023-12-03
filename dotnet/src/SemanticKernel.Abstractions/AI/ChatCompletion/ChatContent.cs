// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

/// <summary>
/// Chat content abstraction
/// </summary>
public class ChatContent : ModelContent
{
    /// <summary>
    /// Role of the author of the message
    /// </summary>
    public AuthorRole Role { get; set; }

    /// <summary>
    /// Content of the message
    /// </summary>
    public string Content { get; set; }

    /// <summary>
    /// Creates a new instance of the <see cref="ChatContent"/> class
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="content">Content of the message</param>
    /// <param name="innerContent">Inner content object reference</param>
    /// <param name="metadata">Dictionary for any additional metadata</param>
    [JsonConstructor]
    public ChatContent(AuthorRole role, string content, object? innerContent = null, IReadOnlyDictionary<string, object?>? metadata = null) : base(innerContent, metadata)
    {
        this.Role = role;
        this.Content = content;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="ChatContent"/> class
    /// </summary>
    /// <param name="chatMessage">Chat message</param>
    /// <param name="metadata">Dictionary for any additional metadata</param>
    public ChatContent(ChatMessage chatMessage, IReadOnlyDictionary<string, object?>? metadata = null) : this(chatMessage.Role, chatMessage.Content, chatMessage, metadata)
    {
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Content ?? string.Empty;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
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
    /// The encoding of the text content.
    /// </summary>
    public Encoding Encoding { get; set; }

    /// <summary>
    /// Creates a new instance of the <see cref="ChatContent"/> class
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="content">Content of the message</param>
    /// <param name="innerContent">Inner content object reference</param>
    /// <param name="encoding">Encoding of the text</param>
    /// <param name="metadata">Dictionary for any additional metadata</param>
    [JsonConstructor]
    public ChatContent(AuthorRole role, string content, object? innerContent = null, Encoding? encoding = null, IReadOnlyDictionary<string, object?>? metadata = null) : base(innerContent, metadata)
    {
        this.Role = role;
        this.Content = content;
        this.Encoding = encoding ?? Encoding.UTF8;
    }

    /// <summary>
    /// Creates a new instance of the <see cref="ChatContent"/> class
    /// </summary>
    /// <param name="chatMessage">Chat message</param>
    /// <param name="encoding">Encoding of the text</param>
    /// <param name="metadata">Dictionary for any additional metadata</param>
    public ChatContent(ChatMessage chatMessage, Encoding? encoding = null, IReadOnlyDictionary<string, object?>? metadata = null) : this(chatMessage.Role, chatMessage.Content, chatMessage, encoding, metadata)
    {
    }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Content ?? string.Empty;
    }
}

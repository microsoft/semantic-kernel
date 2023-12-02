// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

/// <summary>
/// Streaming chat result update.
/// </summary>
public abstract class StreamingChatContent : StreamingContent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="StreamingChatContent"/> class.
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="content">Content of the message</param>
    /// <param name="innerContent">Inner content object reference</param>
    /// <param name="choiceIndex"></param>
    /// <param name="metadata">Additional metadata</param>
    protected StreamingChatContent(AuthorRole? role, string? content, object? innerContent, int choiceIndex = 0, Dictionary<string, object>? metadata = null) : base(innerContent, choiceIndex, metadata)
    {
        this.Role = role;
        this.Content = content;
    }

    /// <summary>
    /// Text associated to the message payload
    /// </summary>
    public string? Content { get; set; }

    /// <summary>
    /// Role of the author of the message
    /// </summary>
    public AuthorRole? Role { get; set; }

    /// <inheritdoc/>
    public override string ToString()
    {
        return this.Content ?? string.Empty;
    }
}

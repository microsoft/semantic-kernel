// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

/// <summary>
/// Chat message abstraction
/// </summary>
public abstract class ChatMessageBase
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
    /// Creates a new instance of the <see cref="ChatMessageBase"/> class
    /// </summary>
    /// <param name="role">Role of the author of the message</param>
    /// <param name="content">Content of the message</param>
    protected ChatMessageBase(AuthorRole role, string content)
    {
        this.Role = role;
        this.Content = content;
    }
}

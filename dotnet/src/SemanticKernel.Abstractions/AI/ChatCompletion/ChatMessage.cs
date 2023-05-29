// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

/// <summary>
/// Chat message abstraction
/// </summary>
public abstract class ChatMessage
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
    /// Creates a new instance of the <see cref="ChatMessage"/> class
    /// </summary>
    /// <param name="Role">Role of the author of the message</param>
    /// <param name="Content">Content of the message</param>
    protected ChatMessage(AuthorRole Role, string Content)
    {
        this.Role = Role;
        this.Content = Content;
    }
}

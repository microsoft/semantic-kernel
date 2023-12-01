// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

/// <summary>
/// Chat content abstraction
/// </summary>
public class ChatContent : CompleteContent
{
    /// <summary>
    /// Role of the author of the message
    /// </summary>
    public AuthorRole Role { get; set; }

    /// <summary>
    /// Content of the message
    /// </summary>
    public string Content { get; protected set; }

    /// <summary>
    /// Creates a new instance of the <see cref="ChatContent"/> class
    /// </summary>
    /// <param name="chatMessage"></param>
    /// <param name="metadata">Dictionary for any additional metadata</param>
    public ChatContent(ChatMessage chatMessage, Dictionary<string, object>? metadata = null) : base(chatMessage, metadata)
    {
        this.Role = chatMessage.Role;
        this.Content = chatMessage.Content;
    }
}

/// <summary>
/// Streaming chat result update.
/// </summary>
public abstract class StreamingChatContent : StreamingContent
{
    /// <summary>
    /// Initializes a new instance of the <see cref="StreamingChatContent"/> class.
    /// </summary>
    /// <param name="innerContent">Inner content object reference</param>
    /// <param name="choiceIndex"></param>
    /// <param name="metadata">Additional metadata</param>
    protected StreamingChatContent(object? innerContent, int choiceIndex = 0, Dictionary<string, object>? metadata = null) : base(innerContent, choiceIndex, metadata)
    {
    }

    /// <summary>
    /// Gets the name of the function to be called
    /// </summary>
    public abstract string? FunctionName { get; protected set; }

    /// <summary>
    /// Gets a function arguments fragment associated with this chunk
    /// </summary>
    public abstract string? FunctionArgument { get; protected set; }

    /// <summary>
    /// Text associated to the message payload
    /// </summary>
    public abstract string? Content { get; protected set; }

    /// <summary>
    /// Role of the author of the message
    /// </summary>
    public abstract AuthorRole? Role { get; protected set; }
}

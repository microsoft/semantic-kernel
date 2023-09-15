// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

#pragma warning disable CA1710

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

/// <summary>
/// Chat message history representation
/// </summary>
public class ChatHistory : List<ChatMessageBase>
{
    private sealed class ChatMessage : ChatMessageBase
    {
        public ChatMessage(AuthorRole authorRole, string content) : base(authorRole, content)
        {
        }
    }

    /// <summary>
    /// List of messages in the chat
    /// </summary>
    public List<ChatMessageBase> Messages => this;

    /// <summary>
    /// Add a message to the chat history
    /// </summary>
    /// <param name="authorRole">Role of the message author</param>
    /// <param name="content">Message content</param>
    public void AddMessage(AuthorRole authorRole, string content)
    {
        this.Add(new ChatMessage(authorRole, content));
    }

    /// <summary>
    /// Insert a message into the chat history
    /// </summary>
    /// <param name="index">Index of the message to insert</param>
    /// <param name="authorRole">Role of the message author</param>
    /// <param name="content">Message content</param>
    public void InsertMessage(int index, AuthorRole authorRole, string content)
    {
        this.Insert(index, new ChatMessage(authorRole, content));
    }

    /// <summary>
    /// Add a user message to the chat history
    /// </summary>
    /// <param name="content">Message content</param>
    public void AddUserMessage(string content)
    {
        this.AddMessage(AuthorRole.User, content);
    }

    /// <summary>
    /// Add an assistant message to the chat history
    /// </summary>
    /// <param name="content">Message content</param>
    public void AddAssistantMessage(string content)
    {
        this.AddMessage(AuthorRole.Assistant, content);
    }

    /// <summary>
    /// Add a system message to the chat history
    /// </summary>
    /// <param name="content">Message content</param>
    public void AddSystemMessage(string content)
    {
        this.AddMessage(AuthorRole.System, content);
    }
}

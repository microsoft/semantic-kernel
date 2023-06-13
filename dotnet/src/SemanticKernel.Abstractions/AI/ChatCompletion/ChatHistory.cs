// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

#pragma warning disable CA1710

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

/// <summary>
/// Chat message history representation
/// </summary>
public class ChatHistory : List<ChatMessageBase>
{
    [Obsolete("This enumeration is deprecated, use AuthorRole struct instead")]
    public enum AuthorRoles
    {
        Unknown = -1,
        System = 0,
        User = 1,
        Assistant = 2,
    }

    private sealed class ChatMessage : ChatMessageBase
    {
        public ChatMessage(AuthorRole authorRole, string content) : base(authorRole, content)
        {
        }
    }

    /// <summary>
    /// Chat message representation
    /// </summary>
    [Obsolete("This class is deprecated, using instances of this class will not be supported")]
    public class Message : ChatMessageBase
    {
        /// <summary>
        /// Role of the message author, e.g. user/assistant/system
        /// </summary>
        public AuthorRoles AuthorRole { get; set; }

        /// <summary>
        /// Create a new instance
        /// </summary>
        /// <param name="authorRole">Role of message author</param>
        /// <param name="content">Message content</param>
        public Message(AuthorRoles authorRole, string content) : base(new AuthorRole(authorRole.ToString()), content)
        {
            this.AuthorRole = authorRole;
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
    [Obsolete("This method with AuthorRoles enumeration is deprecated, use AddMessage(AuthorRole authorRole, string content) instead")]
    public void AddMessage(AuthorRoles authorRole, string content)
    {
        this.Add(new Message(authorRole, content));
    }

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

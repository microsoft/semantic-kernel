// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

#pragma warning disable CA1710

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

public class ChatHistory : List<IChatMessage>
{
    [Obsolete("This enum is deprecated, using it will not be supported")]
    public enum AuthorRoles
    {
        Unknown = -1,
        System = 0,
        User = 1,
        Assistant = 2,
    }

    /// <summary>
    /// Chat message representation
    /// </summary>
    [Obsolete("This class is deprecated, using instances of this class will not be supported")]
    public class Message : IChatMessage
    {
        /// <summary>
        /// Role of the message author, e.g. user/assistant/system
        /// </summary>
        private AuthorRoles AuthorRole { get; set; }

        public string Role => this.AuthorRole.ToString();

        /// <summary>
        /// Message content
        /// </summary>
        public string Content { get; set; }

        /// <summary>
        /// Create a new instance
        /// </summary>
        /// <param name="authorRole">Role of message author</param>
        /// <param name="content">Message content</param>
        public Message(AuthorRoles authorRole, string content)
        {
            this.AuthorRole = authorRole;
            this.Content = content;
        }
    }

    /// <summary>
    /// List of messages in the chat
    /// </summary>
    public List<IChatMessage> Messages => this;

    /// <summary>
    /// Add a message to the chat history
    /// </summary>
    /// <param name="authorRole">Role of the message author</param>
    /// <param name="content">Message content</param>
    [Obsolete("This method is deprecated, use Add(IChatMessage) instead")]
    public void AddMessage(AuthorRoles authorRole, string content)
    {
        this.Add(new Message(authorRole, content));
    }

    /// <summary>
    /// Add a message to the chat history
    /// </summary>
    /// <param name="message">New message instance</param>
    [Obsolete("This method is deprecated, use Add(IChatMessage) instead")]
    public void AddMessage(IChatMessage message)
    {
        this.Add(message);
    }
}

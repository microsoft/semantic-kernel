// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

public class ChatHistory
{
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
    public class Message
    {
        /// <summary>
        /// Role of the message author, e.g. user/assistant/system
        /// </summary>
        public AuthorRoles AuthorRole { get; set; }

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
    public List<Message> Messages { get; }

    /// <summary>
    /// Create a new instance of the chat content class
    /// </summary>
    public ChatHistory()
    {
        this.Messages = new List<Message>();
    }

    /// <summary>
    /// Add a message to the chat history
    /// </summary>
    /// <param name="authorRole">Role of the message author</param>
    /// <param name="content">Message content</param>
    public void AddMessage(AuthorRoles authorRole, string content)
    {
        this.Messages.Add(new Message(authorRole, content));
    }

    public void AddMessage(IChatMessage message)
    {
        if (!Enum.TryParse(message.Role, true, out AuthorRoles role))
        {
            throw new NotSupportedException($"Provided role {message.Role} is not supported");
        }

        this.Messages.Add(new Message(role, message.Content));
    }
}

public interface IChatMessage
{
    string Role { get; }
    string Content { get; }
}

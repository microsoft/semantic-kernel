// Copyright (c) Microsoft. All rights reserved.

using System;
using SemanticKernel.Service.CopilotChat.Storage;

namespace SemanticKernel.Service.CopilotChat.Models;

/// <summary>
/// A chat session
/// </summary>
public class ChatSession : IStorageEntity
{
    /// <summary>
    /// Chat ID that is persistent and unique.
    /// </summary>
    public string Id { get; set; }

    /// <summary>
    /// User ID that is persistent and unique.
    /// </summary>
    public string UserId { get; set; }

    /// <summary>
    /// Title of the chat.
    /// </summary>
    public string Title { get; set; }

    /// <summary>
    /// Timestamp of the chat creation.
    /// </summary>
    public DateTimeOffset CreatedOn { get; set; }

    public ChatSession(string userId, string title)
    {
        this.Id = Guid.NewGuid().ToString();
        this.UserId = userId;
        this.Title = title;
        this.CreatedOn = DateTimeOffset.Now;
    }
}

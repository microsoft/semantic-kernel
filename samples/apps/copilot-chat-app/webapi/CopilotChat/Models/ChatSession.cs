// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;
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
    [JsonPropertyName("id")]
    public string Id { get; set; }

    /// <summary>
    /// Title of the chat.
    /// </summary>
    [JsonPropertyName("title")]
    public string Title { get; set; }

    /// <summary>
    /// Timestamp of the chat creation.
    /// </summary>
    [JsonPropertyName("createdOn")]
    public DateTimeOffset CreatedOn { get; set; }

    /// <summary>
    /// System description of the chat that is used to generate responses.
    /// </summary>
    public string SystemDescription { get; set; }

    /// <summary>
    /// The balance between long term memory and working term memory.
    /// The higher this value, the more the system will rely on long term memory by lowering
    /// the relevance threshold of long term memory and increasing the threshold score of working memory.
    /// </summary>
    public double MemoryBalance { get; set; } = 0.5;

    /// <summary>
    /// Initializes a new instance of the <see cref="ChatSession"/> class.
    /// </summary>
    /// <param name="title">The title of the chat.</param>
    /// <param name="systemDescription">The system description of the chat.</param>
    public ChatSession(string title, string systemDescription)
    {
        this.Id = Guid.NewGuid().ToString();
        this.Title = title;
        this.CreatedOn = DateTimeOffset.Now;
        this.SystemDescription = systemDescription;
    }
}

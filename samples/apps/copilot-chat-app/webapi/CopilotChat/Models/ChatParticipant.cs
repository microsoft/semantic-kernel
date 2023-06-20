// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;
using SemanticKernel.Service.CopilotChat.Storage;

namespace SemanticKernel.Service.CopilotChat.Models;

/// <summary>
/// A chat participant is a user that is part of a chat.
/// A user can be part of multiple chats, thus a user can have multiple chat participants.
/// </summary>
public class ChatParticipant : IStorageEntity
{
    /// <summary>
    /// Participant ID that is persistent and unique.
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; }

    /// <summary>
    /// User ID that is persistent and unique.
    /// </summary>
    [JsonPropertyName("userId")]
    public string UserId { get; set; }

    /// <summary>
    /// Chat ID that this participant belongs to.
    /// </summary>
    [JsonPropertyName("chatId")]
    public string ChatId { get; set; }

    public ChatParticipant(string userId, string chatId)
    {
        this.Id = Guid.NewGuid().ToString();
        this.UserId = userId;
        this.ChatId = chatId;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using SemanticKernel.Service.Storage;

namespace SemanticKernel.Service.Model;

/// <summary>
/// A chat session
/// </summary>
public class ChatParticipant : IStorageEntity
{
    /// <summary>
    /// Chat ID that is persistent and unique.
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

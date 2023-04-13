// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;
using SKWebApi.Storage;

namespace SKWebApi.Skills;

/// <summary>
/// A chat session
/// </summary>
public class Chat : IStorageEntity
{
    /// <summary>
    /// Chat ID that is persistent and unique.
    /// </summary>
    [JsonPropertyName("id")]
    [JsonPropertyOrder(1)]
    public string Id { get; set; }

    /// <summary>
    /// Chat ID that is persistent and unique.
    /// </summary>
    [JsonPropertyName("userId")]
    [JsonPropertyOrder(2)]
    public string UserId { get; set; }

    /// <summary>
    /// Title of the chat.
    /// </summary>
    [JsonPropertyName("title")]
    [JsonPropertyOrder(3)]
    public string Title { get; set; }

    public Chat(string userId, string title)
    {
        this.Id = Guid.NewGuid().ToString();
        this.UserId = userId;
        this.Title = title;
    }
}

/// <summary>
/// Information about a single chat message.
/// </summary>
public class ChatMessage : IStorageEntity
{
    /// <summary>
    /// Timestamp of the message.
    /// </summary>
    [JsonPropertyName("timestamp")]
    [JsonPropertyOrder(1)]
    public DateTimeOffset Timestamp { get; set; }

    /// <summary>
    /// Id of the user who sent this message.
    /// </summary>
    [JsonPropertyName("userId")]
    [JsonPropertyOrder(2)]
    public string UserId { get; set; }

    /// <summary>
    /// Name of the user who sent this message.
    /// </summary>
    [JsonPropertyName("userName")]
    [JsonPropertyOrder(3)]
    public string UserName { get; set; }

    /// <summary>
    /// Id of the chat this message belongs to.
    /// </summary>
    [JsonPropertyName("chatId")]
    [JsonPropertyOrder(4)]
    public string ChatId { get; set; }

    /// <summary>
    /// Content of the message.
    /// </summary>
    [JsonPropertyName("content")]
    [JsonPropertyOrder(5)]
    public string Content { get; set; }

    /// <summary>
    /// Id of the message.
    /// </summary>
    [JsonPropertyName("id")]
    [JsonPropertyOrder(6)]
    public string Id { get; set; }

    /// <summary>
    /// True if the message is from the user. Otherwise it's from the bot.
    /// </summary>
    [JsonPropertyName("fromUser")]
    [JsonPropertyOrder(7)]
    public bool FromUser { get; set; }

    /// <summary>
    /// Create a new chat message. Timestamp is automatically generated.
    /// </summary>
    /// <param name="userId">Id of the user who sent this message</param>
    /// <param name="userName">Name of the user who sent this message</param>
    /// <param name="chatId">The chat ID that this message belongs to</param>
    /// <param name="content">The message</param>
    /// <param name="fromUser">True if the message is from the user. Otherwise it's from the bot.</param>
    public ChatMessage(string userId, string userName, string chatId, string content, bool fromUser = true)
    {
        this.Timestamp = DateTimeOffset.Now;
        this.UserId = userId;
        this.UserName = userName;
        this.ChatId = chatId;
        this.Content = content;
        this.Id = Guid.NewGuid().ToString();
        this.FromUser = fromUser;
    }

    /// <summary>
    /// Create a new chat message for the bot response.
    /// </summary>
    /// <param name="chatId">The chat ID that this message belongs to</param>
    /// <param name="content">The message</param>
    public static ChatMessage CreateBotResponseMessage(string chatId, string content)
    {
        return new ChatMessage("bot", "bot", chatId, content, false);
    }

    /// <summary>
    /// Serialize the object to a formatted string.
    /// </summary>
    /// <returns>A formatted string</returns>
    public string ToFormattedString()
    {
        return $"[{this.Timestamp.ToString("G", CultureInfo.CurrentCulture)}] {this.UserName}: {this.Content}";
    }

    /// <summary>
    /// Serialize the object to a JSON string.
    /// </summary>
    /// <returns>A serialized json string</returns>
    public override string ToString()
    {
        return JsonSerializer.Serialize(this);
    }

    /// <summary>
    /// Deserialize a JSON string to a ChatMessage object.
    /// </summary>
    /// <param name="json">A json string</param>
    /// <returns>A ChatMessage object</returns>
    public static ChatMessage? FromString(string json)
    {
        return JsonSerializer.Deserialize<ChatMessage>(json);
    }
}

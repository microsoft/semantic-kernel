// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace SKWebApi.Skills;

/// <summary>
/// A user in chat.
/// </summary>
public class ChatUser
{
    /// <summary>
    /// User ID that is persistent and unique.
    /// </summary>
    [JsonPropertyName("id")]
    [JsonPropertyOrder(1)]
    public string Id { get; set; }

    /// <summary>
    /// full name of the user.
    /// </summary>
    [JsonPropertyName("fullName")]
    [JsonPropertyOrder(2)]
    public string FullName { get; set; }

    /// <summary>
    /// Email address of the user.
    /// </summary>
    [JsonPropertyName("email")]
    [JsonPropertyOrder(3)]
    public string Email { get; set; }

    /// <summary>
    /// A list of chats that this user is part of.
    /// </summary>
    [JsonPropertyName("chatIds")]
    [JsonPropertyOrder(4)]
    public HashSet<string> ChatIds { get; set; } = new HashSet<string>();

    public ChatUser(string id, string fullName, string email)
    {
        this.Id = id;
        this.FullName = fullName;
        this.Email = email;
    }

    /// <summary>
    /// Add a chat to the list of chats that this user is part of.
    /// </summary>
    public void AddChat(string chatId)
    {
        this.ChatIds.Add(chatId);
    }

    /// <summary>
    /// Override the default ToString() method to serialize the object to JSON.
    /// </summary>
    /// <returns>A serialized json string</returns>
    public override string ToString()
    {
        return JsonSerializer.Serialize(this);
    }

    /// <summary>
    /// Deserialize a JSON string to a ChatUser object.
    /// </summary>
    /// <param name="json">A json string</param>
    /// <returns>A ChatUser object</returns>
    public static ChatUser? FromString(string json)
    {
        return JsonSerializer.Deserialize<ChatUser>(json);
    }
}

/// <summary>
/// A chat session
/// </summary>
public class Chat
{
    /// <summary>
    /// Chat ID that is persistent and unique.
    /// </summary>
    [JsonPropertyName("id")]
    [JsonPropertyOrder(1)]
    public string Id { get; set; }

    /// <summary>
    /// Title of the chat.
    /// </summary>
    public string Title { get; set; }

    /// <summary>
    /// A list of chat messages in this chat.
    /// </summary>
    [JsonPropertyName("messageIds")]
    [JsonPropertyOrder(2)]
    public HashSet<string> MessageIds { get; set; } = new HashSet<string>();

    public Chat(string id, string title)
    {
        this.Id = id;
        this.Title = title;
    }

    /// <summary>
    /// Add a message to the list of messages in this chat.
    /// </summary>
    public void AddMessage(string messageId)
    {
        this.MessageIds.Add(messageId);
    }

    /// <summary>
    /// Override the default ToString() method to serialize the object to JSON.
    /// </summary>
    /// <returns>A serialized json string</returns>
    public override string ToString()
    {
        return JsonSerializer.Serialize(this);
    }

    /// <summary>
    /// Deserialize a JSON string to a Chat object.
    /// </summary>
    /// <param name="json">A json string</param>
    /// <returns>A Chat object</returns>
    public static Chat? FromString(string json)
    {
        return JsonSerializer.Deserialize<Chat>(json);
    }
}

/// <summary>
/// Information about a single chat message.
/// </summary>
public class ChatMessage : IComparable<ChatMessage>
{
    /// <summary>
    /// timestamp of the message.
    /// </summary>
    [JsonPropertyName("timestamp")]
    [JsonPropertyOrder(1)]
    public string Timestamp { get; set; }

    /// <summary>
    /// Id of the sender of the message.
    /// </summary>
    [JsonPropertyName("senderId")]
    [JsonPropertyOrder(2)]
    public string SenderId { get; set; }

    /// <summary>
    /// name of the sender of the message.
    /// </summary>
    [JsonPropertyName("senderName")]
    [JsonPropertyOrder(3)]
    public string SenderName { get; set; }

    /// <summary>
    /// content of the message.
    /// </summary>
    [JsonPropertyName("content")]
    [JsonPropertyOrder(4)]
    public string Content { get; set; }

    /// <summary>
    /// Id of the message.
    /// </summary>
    [JsonPropertyName("id")]
    [JsonPropertyOrder(5)]
    public string Id { get; set; }

    /// <summary>
    /// Create a new chat message. Timestamp is automatically generated.
    /// </summary>
    /// <param name="id"></param>
    /// <param name="senderId"></param>
    /// <param name="senderName"></param>
    /// <param name="content"></param>
    public ChatMessage(string id, string senderId, string senderName, string content)
    {
        this.Timestamp = DateTimeOffset.Now.ToString("G", CultureInfo.CurrentCulture);
        this.SenderId = senderId;
        this.SenderName = senderName;
        this.Content = content;
        this.Id = id;
    }

    /// <summary>
    /// Serialize the object to a formatted string.
    /// </summary>
    /// <returns>A formatted string</returns>
    public string ToFormattedString()
    {
        return $"[{this.Timestamp}] {this.SenderName}: {this.Content}";
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

    /// <summary>
    /// Compare two chat messages by their timestamp. Newer messages are considered smaller.
    /// </summary>
    public int CompareTo(ChatMessage? other)
    {
        if (other == null)
        {
            return 1;
        }

        return other.GetDateTimeOffset().CompareTo(this.GetDateTimeOffset());
    }

    /// <summary>
    /// Get the timestamp as a DateTime object for easier comparison.
    /// </summary>
    /// <returns>A DateTimeOffset object</returns>
    private DateTimeOffset GetDateTimeOffset()
    {
        return DateTimeOffset.ParseExact(this.Timestamp, "G", CultureInfo.CurrentCulture);
    }
}
// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Memory;

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
    /// sender of the message.
    /// </summary>
    [JsonPropertyName("sender")]
    [JsonPropertyOrder(2)]
    public string Sender { get; set; }

    /// <summary>
    /// content of the message.
    /// </summary>
    [JsonPropertyName("content")]
    [JsonPropertyOrder(3)]
    public string Content { get; set; }

    /// <summary>
    /// Id of the message.
    /// </summary>
    public string Id { get; private set; }

    /// <summary>
    /// Create a new chat message. Timestamp is automatically generated.
    /// </summary>
    /// <param name="sender"></param>
    /// <param name="content"></param>
    public ChatMessage(string sender, string content)
    {
        this.Timestamp = DateTimeOffset.Now.ToString("G", CultureInfo.CurrentCulture);
        this.Sender = sender;
        this.Content = content;
        this.Id = $"[{this.Timestamp}] {this.Sender}";
    }

    /// <summary>
    /// Create a new chat message with a specified timestamp.
    /// This is used when deserializing a message from memory.
    /// </summary>
    private ChatMessage(string timestamp, string sender, string content)
    {
        this.Timestamp = timestamp;
        this.Sender = sender;
        this.Content = content;
        this.Id = $"[{this.Timestamp}] {this.Sender}";
    }

    /// <summary>
    /// Override the default ToString() method to serialize the object to a formatted string.
    /// </summary>
    /// <returns>A formatted string</returns>
    public override string ToString()
    {
        return $"{this.Id}: {this.Content}";
    }

    /// <summary>
    /// Serialize the object to a JSON string.
    /// </summary>
    /// <returns>A serialized json string</returns>
    public string ToJsonString()
    {
        return JsonSerializer.Serialize(this);
    }

    /// <summary>
    /// Deserialize a JSON string to a ChatMessage object.
    /// </summary>
    /// <param name="json">A json string</param>
    /// <returns>A ChatMessage object</returns>
    public static ChatMessage? FromJsonString(string json)
    {
        return JsonSerializer.Deserialize<ChatMessage>(json);
    }

    /// <summary>
    /// Deserialize a MemoryRecordMetadata to a ChatMessage object.
    /// </summary>
    /// <param name="memoryMetadata"></param>
    /// <returns>A ChatMessage object</returns>
    /// <exception cref="ArgumentException"></exception>
    public static ChatMessage FromMemoryRecordMetadata(MemoryRecordMetadata memoryMetadata)
    {
        var id = memoryMetadata.Id;
        var text = memoryMetadata.Text;

        if (id.IndexOf(']') == -1)
        {
            throw new ArgumentException("Invalid chat message id: {0}.", id);
        }
        // Extract the timestamp.
        var timestamp = id.Substring(1, id.IndexOf(']') - 1);

        // Extract the sender. Add 2 to skip the "] " after the timestamp.
        var sender = id.Substring(id.IndexOf(']') + 2);

        // Extract the content from the text. Add 2 to skip the ": " after the id.
        var content = text.Substring(id.Length + 2);

        return new ChatMessage(timestamp, sender, content);
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
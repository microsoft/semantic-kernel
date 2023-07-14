// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;
using SemanticKernel.Service.CopilotChat.Storage;

namespace SemanticKernel.Service.CopilotChat.Models;

/// <summary>
/// The external memory source.
/// </summary>
public class MemorySource : IStorageEntity
{
    /// <summary>
    /// Type of the memory source.
    /// </summary>
    public enum MemorySourceType
    {
        // A file source.
        File,
    }

    /// <summary>
    /// Source ID that is persistent and unique.
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// The Chat ID.
    /// </summary>
    [JsonPropertyName("chatId")]
    public string ChatId { get; set; } = string.Empty;

    /// <summary>
    /// The type of the source.
    /// </summary>
    [JsonConverter(typeof(JsonStringEnumConverter))]
    [JsonPropertyName("sourceType")]
    public MemorySourceType SourceType { get; set; } = MemorySourceType.File;

    /// <summary>
    /// The name of the source.
    /// </summary>
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// The external link to the source.
    /// </summary>
    [JsonPropertyName("hyperlink")]
    public Uri? HyperLink { get; set; } = null;

    /// <summary>
    /// The user ID of who shared the source.
    /// </summary>
    [JsonPropertyName("sharedBy")]
    public string SharedBy { get; set; } = string.Empty;

    /// <summary>
    /// When the source is created in the bot.
    /// </summary>
    [JsonPropertyName("createdOn")]
    public DateTimeOffset CreatedOn { get; set; }

    /// <summary>
    /// The size of the source in bytes.
    /// </summary>
    [JsonPropertyName("size")]
    public long Size { get; set; }

    /// <summary>
    /// The number of tokens in the source.
    /// </summary>
    [JsonPropertyName("tokens")]
    public long Tokens { get; set; } = 0;

    /// <summary>
    /// Empty constructor for serialization.
    /// </summary>
    public MemorySource()
    {
    }

    public MemorySource(string chatId, string name, string sharedBy, MemorySourceType type, long size, Uri? hyperlink)
    {
        this.Id = Guid.NewGuid().ToString();
        this.ChatId = chatId;
        this.Name = name;
        this.SourceType = type;
        this.HyperLink = hyperlink;
        this.SharedBy = sharedBy;
        this.CreatedOn = DateTimeOffset.Now;
        this.Size = size;
    }
}

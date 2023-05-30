// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using SemanticKernel.Service.CopilotChat.Storage;

namespace SemanticKernel.Service.CopilotChat.Models;

public enum SourceType
{
    File,
}

/// <summary>
/// The external memory source.
/// TODO: Should this part of the kernel or app?
/// </summary>
public class MemorySource : IStorageEntity
{
    /// <summary>
    /// Source ID that is persistent and unique.
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; }

    /// <summary>
    /// The Chat session id.
    /// </summary>
    [JsonPropertyName("chatSessionId")]
    public string ChatSessionId { get; set; }

    /// <summary>
    /// The type of the source.
    /// </summary>
    [JsonConverter(typeof(JsonStringEnumConverter))]
    [JsonPropertyName("sourceType")]
    public SourceType SourceType { get; set; } = SourceType.File;

    /// <summary>
    /// The name of the source.
    /// </summary>
    [JsonPropertyName("name")]
    public string Name { get; set; }

    /// <summary>
    /// The external link to the source.
    /// </summary>
    [JsonPropertyName("hyperlink")]
    public Uri? HyperLink { get; set; } = null;

    /// <summary>
    /// The user name who shared the source.
    /// </summary>
    [JsonPropertyName("sharedBy")]
    public string SharedBy { get; set; } = string.Empty;

    /// <summary>
    /// When the source is updated in the bot.
    /// </summary>
    [JsonPropertyName("updatedOn")]
    public DateTimeOffset UpdatedOn { get; set; }

    public MemorySource(string chatSessionId, string name, string sharedBy, SourceType type, string? id, Uri? hyperlink)
    {
        this.Id = id ?? Guid.NewGuid().ToString();
        this.ChatSessionId = chatSessionId;
        this.Name = name;
        this.SourceType = type;
        this.HyperLink = hyperlink;
        this.SharedBy = sharedBy;
        this.UpdatedOn = DateTimeOffset.Now;
    }
}

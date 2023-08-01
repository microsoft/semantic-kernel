// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Memory;

/// <summary>
/// Class representing the metadata associated with a Semantic Kernel memory.
/// </summary>
public class MemoryRecordMetadata : ICloneable
{
    /// <summary>
    /// Whether the source data used to calculate embeddings are stored in the local
    /// storage provider or is available through and external service, such as web site, MS Graph, etc.
    /// </summary>
    [JsonInclude]
    [JsonPropertyName("is_reference")]
    public bool IsReference { get; }

    /// <summary>
    /// A value used to understand which external service owns the data, to avoid storing the information
    /// inside the URI. E.g. this could be "MSTeams", "WebSite", "GitHub", etc.
    /// </summary>
    [JsonInclude]
    [JsonPropertyName("external_source_name")]
    public string ExternalSourceName { get; }

    /// <summary>
    /// Unique identifier. The format of the value is domain specific, so it can be a URL, a GUID, etc.
    /// </summary>
    [JsonInclude]
    [JsonPropertyName("id")]
    public string Id { get; }

    /// <summary>
    /// Optional title describing the content. Note: the title is not indexed.
    /// </summary>
    [JsonInclude]
    [JsonPropertyName("description")]
    public string Description { get; }

    /// <summary>
    /// Source text, available only when the memory is not an external source.
    /// </summary>
    [JsonInclude]
    [JsonPropertyName("text")]
    public string Text { get; }

    /// <summary>
    /// Field for saving custom metadata with a memory.
    /// </summary>
    [JsonInclude]
    [JsonPropertyName("additional_metadata")]
    public string AdditionalMetadata { get; }

    /// <summary>
    /// Constructor.
    /// </summary>
    /// <param name="isReference">True if source data is local, false if source data comes from an external service</param>
    /// <param name="id">Unique string used to identify the <see cref="MemoryRecord"/>.</param>
    /// <param name="text">Local source data associated with a <see cref="MemoryRecord"/> embedding.</param>
    /// <param name="description"><see cref="MemoryRecord"/> description.</param>
    /// <param name="externalSourceName">Name of the external source if isReference is true.</param>
    /// <param name="additionalMetadata">Field for saving custom metadata with a memory.</param>
    [JsonConstructor]
    public MemoryRecordMetadata(
        bool isReference,
        string id,
        string text,
        string description,
        string externalSourceName,
        string additionalMetadata
    )
    {
        this.IsReference = isReference;
        this.ExternalSourceName = externalSourceName;
        this.Id = id;
        this.Text = text;
        this.Description = description;
        this.AdditionalMetadata = additionalMetadata;
    }

    /// <summary>
    /// Creates a shallow copy of <see cref="MemoryRecordMetadata"/>.
    /// </summary>
    /// <returns>A shallow copy of this object</returns>
    public object Clone()
    {
        return this.MemberwiseClone();
    }
}

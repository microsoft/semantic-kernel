// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Memory.AzureCognitiveSearch;

/// <summary>
/// Azure Cognitive Search record and index definition.
/// Note: once defined, index cannot be modified.
/// </summary>
public class AzureCognitiveSearchMemoryRecord
{
    public const string IdField = "Id";
    public const string TextField = "Text";
    public const string EmbeddingField = "Embedding";
    public const string ExternalSourceNameField = "ExternalSourceName";
    public const string DescriptionField = "Description";
    public const string AdditionalMetadataField = "AdditionalMetadata";
    public const string IsReferenceField = "IsReference";

    /// <summary>
    /// Record Id.
    /// The record is not filterable to save quota, also SK uses only semantic search.
    /// </summary>
    [JsonPropertyName(IdField)]
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// Content is stored here.
    /// </summary>
    [JsonPropertyName(TextField)]
    public string? Text { get; set; } = string.Empty;

    /// <summary>
    /// Content embedding
    /// </summary>
    [JsonPropertyName(EmbeddingField)]
    [JsonConverter(typeof(ReadOnlyMemoryConverter))]
    public ReadOnlyMemory<float> Embedding { get; set; }

    /// <summary>
    /// Optional description of the content, e.g. a title. This can be useful when
    /// indexing external data without pulling in the entire content.
    /// </summary>
    [JsonPropertyName(DescriptionField)]
    public string? Description { get; set; } = string.Empty;

    /// <summary>
    /// Additional metadata. Currently this is a string, where you could store serialized data as JSON.
    /// In future the design might change to allow storing named values and leverage filters.
    /// </summary>
    [JsonPropertyName(AdditionalMetadataField)]
    public string? AdditionalMetadata { get; set; } = string.Empty;

    /// <summary>
    /// Name of the external source, in cases where the content and the Id are
    /// referenced to external information.
    /// </summary>
    [JsonPropertyName(ExternalSourceNameField)]
    public string ExternalSourceName { get; set; } = string.Empty;

    /// <summary>
    /// Whether the record references external information.
    /// </summary>
    [JsonPropertyName(IsReferenceField)]
    public bool IsReference { get; set; } = false;

    /// <summary>
    /// Ctor required by JSON deserializer
    /// </summary>
    public AzureCognitiveSearchMemoryRecord()
    {
    }

    public AzureCognitiveSearchMemoryRecord(string id)
    {
        this.Id = EncodeId(id);
    }

    public AzureCognitiveSearchMemoryRecord(
        string id,
        string text,
        string externalSourceName,
        bool isReference,
        ReadOnlyMemory<float> embedding,
        string? description = null,
        string? additionalMetadata = null)
    {
        this.Id = EncodeId(id);
        this.IsReference = isReference;
        this.Embedding = embedding;
        this.Text = text;
        this.ExternalSourceName = externalSourceName;
        this.Description = description;
        this.AdditionalMetadata = additionalMetadata;
    }

    public MemoryRecordMetadata ToMemoryRecordMetadata()
    {
        return new MemoryRecordMetadata(
            isReference: this.IsReference,
            id: DecodeId(this.Id),
            text: this.Text ?? string.Empty,
            description: this.Description ?? string.Empty,
            externalSourceName: this.ExternalSourceName,
            additionalMetadata: this.AdditionalMetadata ?? string.Empty);
    }

    public static AzureCognitiveSearchMemoryRecord FromMemoryRecord(MemoryRecord record)
    {
        return new AzureCognitiveSearchMemoryRecord(
            id: record.Metadata.Id,
            text: record.Metadata.Text,
            externalSourceName: string.Empty,
            isReference: record.Metadata.IsReference,
            description: record.Metadata.Description,
            additionalMetadata: record.Metadata.AdditionalMetadata,
            embedding: record.Embedding
        );
    }

    public MemoryRecord ToMemoryRecord(bool withEmbeddings = true)
    {
        return new MemoryRecord(
            metadata: this.ToMemoryRecordMetadata(),
            embedding: withEmbeddings ? this.Embedding : default,
            key: this.Id);
    }

    /// <summary>
    /// ACS keys can contain only letters, digits, underscore, dash, equal sign, recommending
    /// to encode values with a URL-safe algorithm.
    /// </summary>
    /// <param name="realId">Original Id</param>
    /// <returns>Encoded id</returns>
    protected internal static string EncodeId(string realId)
    {
        var bytes = Encoding.UTF8.GetBytes(realId);
        return Convert.ToBase64String(bytes);
    }

    private protected static string DecodeId(string encodedId)
    {
        var bytes = Convert.FromBase64String(encodedId);
        return Encoding.UTF8.GetString(bytes);
    }
}

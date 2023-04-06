// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel.AI.Embeddings;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// IMPORTANT: this is a storage schema. Changing the fields will invalidate existing metadata stored in persistent vector DBs.
/// </summary>
public class MemoryRecord : IEmbeddingWithMetadata<float>
{
    /// <summary>
    /// Source content embeddings.
    /// </summary>
    public Embedding<float> Embedding { get; }

    /// <summary>
    /// Metadata associated with a Semantic Kernel memory.
    /// </summary>
    public MemoryRecordMetadata Metadata { get; }

    /// <summary>
    /// Prepare an instance about a memory which source is stored externally.
    /// The universal resource identifies points to the URL (or equivalent) to find the original source.
    /// </summary>
    /// <param name="externalId">URL (or equivalent) to find the original source</param>
    /// <param name="sourceName">Name of the external service, e.g. "MSTeams", "GitHub", "WebSite", "Outlook IMAP", etc.</param>
    /// <param name="description">Optional description of the record. Note: the description is not indexed.</param>
    /// <param name="embedding">Source content embeddings</param>
    /// <returns>Memory record</returns>
    public static MemoryRecord ReferenceRecord(
        string externalId,
        string sourceName,
        string? description,
        Embedding<float> embedding)
    {
        return new MemoryRecord(
            new MemoryRecordMetadata
            (
                isReference: true,
                externalSourceName: sourceName,
                id: externalId,
                description: description ?? string.Empty,
                text: string.Empty
            ),
            embedding
        );
    }

    /// <summary>
    /// Prepare an instance for a memory stored in the internal storage provider.
    /// </summary>
    /// <param name="id">Resource identifier within the storage provider, e.g. record ID/GUID/incremental counter etc.</param>
    /// <param name="text">Full text used to generate the embeddings</param>
    /// <param name="description">Optional description of the record. Note: the description is not indexed.</param>
    /// <param name="embedding">Source content embeddings</param>
    /// <returns>Memory record</returns>
    public static MemoryRecord LocalRecord(
        string id,
        string text,
        string? description,
        Embedding<float> embedding)
    {
        return new MemoryRecord
        (
            new MemoryRecordMetadata
            (
                isReference: false,
                id: id,
                text: text,
                description: description ?? string.Empty,
                externalSourceName: string.Empty
            ),
            embedding
        );
    }

    public static MemoryRecord FromJson(
        string json,
        Embedding<float> embedding)
    {
        var metadata = JsonSerializer.Deserialize<MemoryRecordMetadata>(json);
        if (metadata != null)
        {
            return new MemoryRecord(metadata, embedding);
        }

        throw new MemoryException(
            MemoryException.ErrorCodes.UnableToDeserializeMetadata,
            "Unable to create memory record from serialized metadata");
    }

    public string GetSerializedMetadata()
    {
        return JsonSerializer.Serialize(this.Metadata);
    }

    /// <summary>
    /// Block constructor, use <see cref="ReferenceRecord"/> or <see cref="LocalRecord"/>
    /// </summary>
    private MemoryRecord(MemoryRecordMetadata metadata, Embedding<float> embedding)
    {
        this.Metadata = metadata;
        this.Embedding = embedding;
    }
}

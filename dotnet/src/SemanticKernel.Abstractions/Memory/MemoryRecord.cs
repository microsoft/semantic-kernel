<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
﻿// Copyright (c) Microsoft. All rights reserved.
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> origin/main
=======
// Copyright (c) Microsoft. All rights reserved.
>>>>>>> Stashed changes

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
>>>>>>> Stashed changes
=======
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
>>>>>>> Stashed changes
=======
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
>>>>>>> Stashed changes
=======
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
>>>>>>> Stashed changes
=======
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
>>>>>>> Stashed changes
=======
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
>>>>>>> origin/main
=======
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Diagnostics;
>>>>>>> Stashed changes

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// IMPORTANT: this is a storage schema. Changing the fields will invalidate existing metadata stored in persistent vector DBs.
/// </summary>
[Experimental("SKEXP0001")]
public class MemoryRecord : DataEntryBase
{
    /// <summary>
    /// Source content embeddings.
    /// </summary>
    [JsonPropertyName("embedding")]
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    [JsonConverter(typeof(ReadOnlyMemoryConverter))]
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    public ReadOnlyMemory<float> Embedding { get; }

    /// <summary>
    /// Metadata associated with a Semantic Kernel memory.
    /// </summary>
    [JsonPropertyName("metadata")]
    public MemoryRecordMetadata Metadata { get; }

    /// <summary>
    /// Constructor, use <see cref="ReferenceRecord"/> or <see cref="LocalRecord"/>
    /// </summary>
    [JsonConstructor]
    public MemoryRecord(
        MemoryRecordMetadata metadata,
        ReadOnlyMemory<float> embedding,
        string? key,
        DateTimeOffset? timestamp = null) : base(key, timestamp)
    {
        this.Metadata = metadata;
        this.Embedding = embedding;
    }

    /// <summary>
    /// Prepare an instance about a memory which source is stored externally.
    /// The universal resource identifies points to the URL (or equivalent) to find the original source.
    /// </summary>
    /// <param name="externalId">URL (or equivalent) to find the original source.</param>
    /// <param name="sourceName">Name of the external service, e.g. "MSTeams", "GitHub", "WebSite", "Outlook IMAP", etc.</param>
    /// <param name="description">Optional description of the record. Note: the description is not indexed.</param>
    /// <param name="embedding">Source content embedding.</param>
    /// <param name="additionalMetadata">Optional string for saving custom metadata.</param>
    /// <param name="key">Optional existing database key.</param>
    /// <param name="timestamp">optional timestamp.</param>
    /// <returns>Memory record</returns>
    public static MemoryRecord ReferenceRecord(
        string externalId,
        string sourceName,
        string? description,
        ReadOnlyMemory<float> embedding,
        string? additionalMetadata = null,
        string? key = null,
        DateTimeOffset? timestamp = null)
    {
        return new MemoryRecord(
            new MemoryRecordMetadata
            (
                isReference: true,
                externalSourceName: sourceName,
                id: externalId,
                description: description ?? string.Empty,
                text: string.Empty,
                additionalMetadata: additionalMetadata ?? string.Empty
            ),
            embedding,
            key,
            timestamp
        );
    }

    /// <summary>
    /// Prepare an instance for a memory stored in the internal storage provider.
    /// </summary>
    /// <param name="id">Resource identifier within the storage provider, e.g. record ID/GUID/incremental counter etc.</param>
    /// <param name="text">Full text used to generate the embeddings.</param>
    /// <param name="description">Optional description of the record. Note: the description is not indexed.</param>
    /// <param name="embedding">Source content embedding.</param>
    /// <param name="additionalMetadata">Optional string for saving custom metadata.</param>
    /// <param name="key">Optional existing database key.</param>
    /// <param name="timestamp">Optional timestamp.</param>
    /// <returns>Memory record</returns>
    public static MemoryRecord LocalRecord(
        string id,
        string text,
        string? description,
        ReadOnlyMemory<float> embedding,
        string? additionalMetadata = null,
        string? key = null,
        DateTimeOffset? timestamp = null)
    {
        return new MemoryRecord
        (
            new MemoryRecordMetadata
            (
                isReference: false,
                id: id,
                text: text,
                description: description ?? string.Empty,
                externalSourceName: string.Empty,
                additionalMetadata: additionalMetadata ?? string.Empty
            ),
            embedding,
            key,
            timestamp
        );
    }

    /// <summary>
    /// Create a memory record from a serialized metadata string.
    /// </summary>
    /// <param name="json">Json string representing a memory record's metadata.</param>
    /// <param name="embedding">Optional embedding associated with a memory record.</param>
    /// <param name="key">Optional existing database key.</param>
    /// <param name="timestamp">optional timestamp.</param>
    /// <returns>Memory record</returns>
    /// <exception cref="KernelException"></exception>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
    /// <exception cref="SKException"></exception>
    /// <exception cref="SKException"></exception>
>>>>>>> Stashed changes
=======
    /// <exception cref="SKException"></exception>
    /// <exception cref="SKException"></exception>
>>>>>>> Stashed changes
=======
    /// <exception cref="SKException"></exception>
    /// <exception cref="SKException"></exception>
>>>>>>> Stashed changes
=======
    /// <exception cref="SKException"></exception>
    /// <exception cref="SKException"></exception>
>>>>>>> Stashed changes
=======
    /// <exception cref="SKException"></exception>
    /// <exception cref="SKException"></exception>
>>>>>>> Stashed changes
=======
    /// <exception cref="SKException"></exception>
    /// <exception cref="SKException"></exception>
>>>>>>> origin/main
=======
    /// <exception cref="SKException"></exception>
    /// <exception cref="SKException"></exception>
>>>>>>> Stashed changes
    public static MemoryRecord FromJsonMetadata(
        string json,
        ReadOnlyMemory<float> embedding,
        string? key = null,
        DateTimeOffset? timestamp = null)
    {
        var metadata = JsonSerializer.Deserialize<MemoryRecordMetadata>(json);
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        return metadata is not null
            ? new MemoryRecord(metadata, embedding, key, timestamp)
            : throw new KernelException("Unable to create memory record from serialized metadata");
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
        var metadata = JsonSerializer.Deserialize<MemoryRecordMetadata>(json, MemoryRecordMetadataJsonSerializerContext.Default.MemoryRecordMetadata);
>>>>>>> origin/main
        return metadata is not null
            ? new MemoryRecord(metadata, embedding, key, timestamp)
            : throw new KernelException("Unable to create memory record from serialized metadata");
        return metadata != null
            ? new MemoryRecord(metadata, embedding ?? Embedding<float>.Empty, key, timestamp)
            : throw new SKException("Unable to create memory record from serialized metadata");
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        var metadata = JsonSerializer.Deserialize<MemoryRecordMetadata>(json, MemoryRecordMetadataJsonSerializerContext.Default.MemoryRecordMetadata);
        return metadata is not null
            ? new MemoryRecord(metadata, embedding, key, timestamp)
            : throw new KernelException("Unable to create memory record from serialized metadata");
        return metadata != null
            ? new MemoryRecord(metadata, embedding ?? Embedding<float>.Empty, key, timestamp)
            : throw new SKException("Unable to create memory record from serialized metadata");
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    }

    /// <summary>
    /// Create a memory record from a memory record's metadata.
    /// </summary>
    /// <param name="metadata">Metadata associated with a memory.</param>
    /// <param name="embedding">Optional embedding associated with a memory record.</param>
    /// <param name="key">Optional existing database key.</param>
    /// <param name="timestamp">optional timestamp.</param>
    /// <returns>Memory record</returns>
    public static MemoryRecord FromMetadata(
        MemoryRecordMetadata metadata,
        ReadOnlyMemory<float> embedding,
        string? key = null,
        DateTimeOffset? timestamp = null)
    {
        return new MemoryRecord(metadata, embedding, key, timestamp);
    }

    /// <summary>
    /// Serialize the metadata of a memory record.
    /// </summary>
    /// <returns>The memory record's metadata serialized to a json string.</returns>
    public string GetSerializedMetadata()
    {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        return JsonSerializer.Serialize(this.Metadata);
=======
        return JsonSerializer.Serialize(this.Metadata, MemoryRecordMetadataJsonSerializerContext.Default.MemoryRecordMetadata);
>>>>>>> Stashed changes
=======
        return JsonSerializer.Serialize(this.Metadata, MemoryRecordMetadataJsonSerializerContext.Default.MemoryRecordMetadata);
>>>>>>> Stashed changes
=======
        return JsonSerializer.Serialize(this.Metadata, MemoryRecordMetadataJsonSerializerContext.Default.MemoryRecordMetadata);
>>>>>>> Stashed changes
=======
        return JsonSerializer.Serialize(this.Metadata, MemoryRecordMetadataJsonSerializerContext.Default.MemoryRecordMetadata);
>>>>>>> Stashed changes
=======
        return JsonSerializer.Serialize(this.Metadata, MemoryRecordMetadataJsonSerializerContext.Default.MemoryRecordMetadata);
>>>>>>> Stashed changes
=======
        return JsonSerializer.Serialize(this.Metadata, MemoryRecordMetadataJsonSerializerContext.Default.MemoryRecordMetadata);
>>>>>>> origin/main
=======
        return JsonSerializer.Serialize(this.Metadata, MemoryRecordMetadataJsonSerializerContext.Default.MemoryRecordMetadata);
>>>>>>> Stashed changes
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using Kusto.Cloud.Platform.Utils;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.Kusto;

/// <summary>
/// Kusto memory record entity.
/// </summary>
public sealed class KustoMemoryRecord
{
    /// <summary>
    /// Entity key.
    /// </summary>
    public string Key { get; set; }

    /// <summary>
    /// Metadata associated with memory entity.
    /// </summary>
    public MemoryRecordMetadata Metadata { get; set; }

    /// <summary>
    /// Source content embedding.
    /// </summary>
    public Embedding<float> Embedding { get; set; }

    /// <summary>
    /// Optional timestamp.
    /// </summary>
    public DateTimeOffset? Timestamp { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KustoMemoryRecord"/> class.
    /// </summary>
    /// <param name="record">Instance of <see cref="MemoryRecord"/>.</param>
    public KustoMemoryRecord(MemoryRecord record) : this(record.Key, record.Metadata, record.Embedding, record.Timestamp) { }

    /// <summary>
    /// Initializes a new instance of the <see cref="KustoMemoryRecord"/> class.
    /// </summary>
    /// <param name="key">Entity key.</param>
    /// <param name="metadata">Metadata associated with memory entity.</param>
    /// <param name="embedding">Source content embedding.</param>
    /// <param name="timestamp">Optional timestamp.</param>
    public KustoMemoryRecord(string key, MemoryRecordMetadata metadata, Embedding<float> embedding, DateTimeOffset? timestamp = null)
    {
        this.Key = key;
        this.Metadata = metadata;
        this.Embedding = embedding;
        this.Timestamp = timestamp;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KustoMemoryRecord"/> class.
    /// </summary>
    /// <param name="key">Entity key.</param>
    /// <param name="metadata">Serialized metadata associated with memory entity.</param>
    /// <param name="embedding">Source content embedding.</param>
    /// <param name="timestamp">Optional timestamp.</param>
    public KustoMemoryRecord(string key, string metadata, string? embedding, string? timestamp = null)
    {
        this.Key = key;
        this.Metadata = KustoSerializer.DeserializeMetadata(metadata);
        this.Embedding = KustoSerializer.DeserializeEmbedding(embedding);
        this.Timestamp = KustoSerializer.DeserializeDateTimeOffset(timestamp);
    }

    /// <summary>
    /// Returns instance of mapped <see cref="MemoryRecord"/>.
    /// </summary>
    public MemoryRecord ToMemoryRecord()
    {
        return new MemoryRecord(this.Metadata, this.Embedding, this.Key, this.Timestamp);
    }

    /// <summary>
    /// Writes properties of <see cref="KustoMemoryRecord"/> instance to stream using <see cref="CsvWriter"/>.
    /// </summary>
    /// <param name="streamWriter">Instance of <see cref="CsvWriter"/> to write properties to stream.</param>
    public void WriteToCsvStream(CsvWriter streamWriter)
    {
        var jsonifiedMetadata = KustoSerializer.SerializeMetadata(this.Metadata);
        var jsonifiedEmbedding = KustoSerializer.SerializeEmbedding(this.Embedding);
        var isoFormattedDate = KustoSerializer.SerializeDateTimeOffset(this.Timestamp);

        streamWriter.WriteField(this.Key);
        streamWriter.WriteField(jsonifiedMetadata);
        streamWriter.WriteField(jsonifiedEmbedding);
        streamWriter.WriteField(isoFormattedDate);
        streamWriter.CompleteRecord();
    }
}

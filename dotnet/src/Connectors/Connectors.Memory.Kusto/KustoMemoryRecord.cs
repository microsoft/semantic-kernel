// Copyright (c) Microsoft. All rights reserved.

using System;
using Kusto.Cloud.Platform.Utils;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.Kusto;

sealed public class KustoMemoryRecord
{
    public string Key { get; set; }
    public MemoryRecordMetadata Metadata { get; set; }
    public Embedding<float> Embedding { get; set; }
    public DateTime? Timestamp { get; set; }

    public KustoMemoryRecord(MemoryRecord record) : this(record.Key, record.Metadata, record.Embedding, record.Timestamp?.UtcDateTime) { }

    public KustoMemoryRecord(string key, MemoryRecordMetadata metadata, Embedding<float> embedding, DateTime? timestamp = null)
    {
        this.Key = key;
        this.Metadata = metadata;
        this.Embedding = embedding;
        this.Timestamp = timestamp;
    }

    public KustoMemoryRecord(string key, string metadata, string? embedding, DateTime? timestamp = null)
    {
        this.Key = key;
        this.Metadata = KustoSerializer.DeserializeMetadata(metadata);
        this.Embedding = KustoSerializer.DeserializeEmbedding(embedding);
        this.Timestamp = timestamp;
    }

    public MemoryRecord ToMemoryRecord()
    {
        return new MemoryRecord(this.Metadata, this.Embedding, this.Key, this.Timestamp);
    }

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

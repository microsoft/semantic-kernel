// Copyright (c) Microsoft.All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.Json;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone;

public static class PineconeDocumentExtensions
{
    public static PineconeDocument ToPineconeDocument(this MemoryRecord memoryRecord)
    {
        JsonSerializerOptions options = PineconeUtils.DefaultSerializerOptions;

        Dictionary<string, object>? metadata = JsonSerializer.Deserialize<Dictionary<string, object>>(memoryRecord.Metadata.AdditionalMetadata, options) ??
                                               new Dictionary<string, object>();

        metadata["document_Id"] = memoryRecord.Metadata.Id;
        metadata["text"] = memoryRecord.Metadata.Text;
        metadata["source_Id"] = memoryRecord.Metadata.ExternalSourceName;

        if (memoryRecord.HasTimestamp)
        {
            metadata["created_at"] = memoryRecord.Timestamp?.ToString("o") ?? DateTimeOffset.UtcNow.ToString("o");
        }

        return PineconeDocument.Create(memoryRecord.Key, memoryRecord.Embedding.Vector)
            .WithMetadata(metadata);
    }

    public static MemoryRecord ToMemoryRecord(this PineconeDocument pineconeDocument)
    {
        Embedding<float> embedding = new(pineconeDocument.Values);

        string additionalMetadataJson = pineconeDocument.GetSerializedMetadata();

        MemoryRecordMetadata memoryRecordMetadata = new(
            false,
            pineconeDocument.DocumentId ?? string.Empty,
            pineconeDocument.Text ?? string.Empty,
            string.Empty,
            pineconeDocument.SourceId ?? string.Empty,
            additionalMetadataJson
        );

        DateTimeOffset? timestamp = pineconeDocument.CreatedAt != null
            ? DateTimeOffset.Parse(pineconeDocument.CreatedAt.ToString(), DateTimeFormatInfo.InvariantInfo)
            : null;

        return MemoryRecord.FromMetadata(memoryRecordMetadata, embedding, pineconeDocument.Id, timestamp);

    }
}

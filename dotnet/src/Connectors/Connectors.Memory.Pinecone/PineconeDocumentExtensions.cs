// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.Json;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

#pragma warning disable SKEXP0001 // IMemoryStore is experimental (but we're obsoleting)

/// <summary>
/// Extensions for <see cref="PineconeDocument"/> class.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
public static class PineconeDocumentExtensions
{
    /// <summary>
    /// Maps <see cref="MemoryRecord"/> instance to <see cref="PineconeDocument"/>.
    /// </summary>
    /// <param name="memoryRecord">Instance of <see cref="MemoryRecord"/>.</param>
    /// <returns>Instance of <see cref="PineconeDocument"/>.</returns>
    public static PineconeDocument ToPineconeDocument(this MemoryRecord memoryRecord)
    {
        string key = !string.IsNullOrEmpty(memoryRecord.Key)
            ? memoryRecord.Key
            : memoryRecord.Metadata.Id;

        Dictionary<string, object> metadata = new()
        {
            ["document_Id"] = memoryRecord.Metadata.Id,
            ["text"] = memoryRecord.Metadata.Text,
            ["source_Id"] = memoryRecord.Metadata.ExternalSourceName,
            ["created_at"] = memoryRecord.HasTimestamp
                ? memoryRecord.Timestamp?.ToString("o") ?? DateTimeOffset.UtcNow.ToString("o")
                : DateTimeOffset.UtcNow.ToString("o")
        };

        if (!string.IsNullOrEmpty(memoryRecord.Metadata.AdditionalMetadata))
        {
            JsonSerializerOptions options = PineconeUtils.DefaultSerializerOptions;
            var additionalMetaData = JsonSerializer.Deserialize<Dictionary<string, object>>(memoryRecord.Metadata.AdditionalMetadata, options);

            if (additionalMetaData is not null)
            {
                foreach (var item in additionalMetaData)
                {
                    metadata[item.Key] = item.Value;
                }
            }
        }

        return PineconeDocument
            .Create(key, memoryRecord.Embedding)
            .WithMetadata(metadata);
    }

    /// <summary>
    /// Maps <see cref="PineconeDocument"/> instance to <see cref="MemoryRecord"/>.
    /// </summary>
    /// <param name="pineconeDocument">Instance of <see cref="PineconeDocument"/>.</param>
    /// <returns>Instance of <see cref="MemoryRecord"/>.</returns>
    public static MemoryRecord ToMemoryRecord(this PineconeDocument pineconeDocument)
    {
        ReadOnlyMemory<float> embedding = pineconeDocument.Values;

        string additionalMetadataJson = pineconeDocument.GetSerializedMetadata();

        MemoryRecordMetadata memoryRecordMetadata = new(
            false,
            pineconeDocument.DocumentId ?? string.Empty,
            pineconeDocument.Text ?? string.Empty,
            string.Empty,
            pineconeDocument.SourceId ?? string.Empty,
            additionalMetadataJson
        );

        DateTimeOffset? timestamp = pineconeDocument.CreatedAt is not null
            ? DateTimeOffset.Parse(pineconeDocument.CreatedAt, DateTimeFormatInfo.InvariantInfo)
            : null;

        return MemoryRecord.FromMetadata(memoryRecordMetadata, embedding, pineconeDocument.Id, timestamp);
    }
}

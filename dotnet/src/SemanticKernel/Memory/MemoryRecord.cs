// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel.AI.Embeddings;

namespace Microsoft.SemanticKernel.Memory;

/// <summary>
/// IMPORTANT: this is a storage schema. Changing the fields will invalidate existing metadata stored in persistent vector DBs.
/// </summary>
internal class MemoryRecord : IEmbeddingWithMetadata<float>
{
    /// <summary>
    /// Nested class representing the metadata associated with a Semantic Kernel memory.
    /// </summary>
    public class MemoryRecordMetadata
    {
        /// <summary>
        /// Whether the source data used to calculate embeddings are stored in the local
        /// storage provider or is available through and external service, such as web site, MS Graph, etc.
        /// </summary>
        public bool IsReference { get; }

        /// <summary>
        /// A value used to understand which external service owns the data, to avoid storing the information
        /// inside the URI. E.g. this could be "MSTeams", "WebSite", "GitHub", etc.
        /// </summary>
        public string ExternalSourceName { get; }

        /// <summary>
        /// Unique identifier. The format of the value is domain specific, so it can be a URL, a GUID, etc.
        /// </summary>
        public string Id { get; }

        /// <summary>
        /// Optional title describing the content. Note: the title is not indexed.
        /// </summary>
        public string Description { get; }

        /// <summary>
        /// Source text, available only when the memory is not an external source.
        /// </summary>
        public string Text { get; }

        internal MemoryRecordMetadata(
            bool isReference,
            string id,
            string? text = null,
            string? description = null,
            string? externalSource = null
        )
        {
            this.IsReference = isReference;
            this.ExternalSourceName = externalSource ?? string.Empty;
            this.Id = id;
            this.Text = text ?? string.Empty;
            this.Description = description ?? string.Empty;
        }
    }

    /// <summary>
    /// Source content embeddings.
    /// </summary>
    public Embedding<float> Embedding { get; private set; }

    public MemoryRecordMetadata Metadata { get; private set; }

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
        return new MemoryRecord
        {
            Metadata = new MemoryRecordMetadata
            (
                isReference: true,
                externalSource: sourceName,
                id: externalId,
                description: description
            ),
            Embedding = embedding
        };
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
        {
            Metadata = new MemoryRecordMetadata
            (
                isReference: false,
                id: id,
                text: text,
                description: description
            ),
            Embedding = embedding
        };
    }

    public static MemoryRecord FromJson(
        string json,
        Embedding<float> embedding)
    {
        var metadata = JsonSerializer.Deserialize<MemoryRecordMetadata>(json);
        if (metadata != null)
        {
            return new MemoryRecord
            {
                Metadata = metadata,
                Embedding = embedding
            };
        }
        else
        {
            throw new MemoryException(
                MemoryException.ErrorCodes.UnableToSerializeMetadata,
                "Unable to create memory from serialized metadata");
        }
    }

    public string JsonSerializeMetadata()
    {
        return JsonSerializer.Serialize(this.Metadata);
    }

    /// <summary>
    /// Block constructor, use <see cref="ReferenceRecord"/> or <see cref="LocalRecord"/>
    /// </summary>
    private MemoryRecord()
    {
    }
}

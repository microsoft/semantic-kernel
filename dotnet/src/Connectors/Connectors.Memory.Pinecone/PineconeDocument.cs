// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Pinecone Document entity.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
public class PineconeDocument
{
    /// <summary>
    /// The unique ID of a Document
    /// </summary>
    /// <value>The unique ID of a document</value>
    [JsonPropertyName("id")]
    public string Id { get; set; }

    /// <summary>
    /// Vector dense data. This should be the same length as the dimension of the index being queried.
    /// </summary>
    [JsonPropertyName("values")]
    public ReadOnlyMemory<float> Values { get; set; }

    /// <summary>
    /// The metadata associated with the document
    /// </summary>
    [JsonPropertyName("metadata")]
    public Dictionary<string, object>? Metadata { get; set; }

    /// <summary>
    /// Gets or Sets SparseValues
    /// </summary>
    [JsonPropertyName("sparseValues")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public SparseVectorData? SparseValues { get; set; }

    /// <summary>
    /// Gets or Sets Score
    /// </summary>
    [JsonPropertyName("score")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public float? Score { get; set; }

    /// <summary>
    ///  The text of the document, if the document was created from text.
    /// </summary>
    [JsonIgnore]
    public string? Text => this.Metadata?.TryGetValue("text", out var text) == true ? text.ToString() : null;

    /// <summary>
    /// The document ID, used to identify the source text this document was created from
    /// </summary>
    /// <remarks>
    ///  An important distinction between the document ID and ID / Key is that the document ID is
    ///  used to identify the source text this document was created from, while the ID / Key is used
    ///  to identify the document itself.
    /// </remarks>
    [JsonIgnore]
    public string? DocumentId => this.Metadata?.TryGetValue("document_Id", out var docId) == true ? docId.ToString() : null;

    /// <summary>
    /// The source ID, used to identify the source text this document was created from.
    /// </summary>
    /// <remarks>
    ///  An important distinction between the source ID and the source of the document is that the source
    ///  may be Medium, Twitter, etc. while the source ID would be the ID of the Medium post, Twitter tweet, etc.
    /// </remarks>
    [JsonIgnore]
    public string? SourceId => this.Metadata?.TryGetValue("source_Id", out var sourceId) == true ? sourceId.ToString() : null;

    /// <summary>
    /// The timestamp, used to identify when document was created.
    /// </summary>
    [JsonIgnore]
    public string? CreatedAt => this.Metadata?.TryGetValue("created_at", out var createdAt) == true ? createdAt.ToString() : null;

    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeDocument" /> class.
    /// </summary>
    /// <param name="values">Vector dense data. This should be the same length as the dimension of the index being queried.</param>
    /// <param name="id">The unique ID of a vector.</param>
    /// <param name="metadata">metadata.</param>
    /// <param name="sparseValues">sparseValues.</param>
    /// <param name="score"></param>
    [JsonConstructor]
    public PineconeDocument(
        ReadOnlyMemory<float> values = default,
        string? id = default,
        Dictionary<string, object>? metadata = null,
        SparseVectorData? sparseValues = null,
        float? score = null)
    {
        this.Id = id ?? Guid.NewGuid().ToString();
        this.Values = values;
        this.Metadata = metadata ?? [];
        this.SparseValues = sparseValues;
        this.Score = score;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeDocument" /> class.
    /// </summary>
    /// <param name="id">The unique ID of a vector.</param>
    /// <param name="values">Vector dense data. This should be the same length as the dimension of the index being queried.</param>
    public static PineconeDocument Create(string? id = default, ReadOnlyMemory<float> values = default)
    {
        return new PineconeDocument(values, id);
    }

    /// <summary>
    /// Sets sparse vector data for <see cref="PineconeDocument" /> class.
    /// </summary>
    /// <param name="sparseValues">Vector sparse data. Represented as a list of indices and a list of corresponded values, which must be the same length.</param>
    public PineconeDocument WithSparseValues(SparseVectorData? sparseValues)
    {
        this.SparseValues = sparseValues;
        return this;
    }

    /// <summary>
    /// Sets metadata for <see cref="PineconeDocument" /> class.
    /// </summary>
    /// <param name="metadata">The metadata associated with the document.</param>
    public PineconeDocument WithMetadata(Dictionary<string, object>? metadata)
    {
        this.Metadata = metadata;
        return this;
    }

    /// <summary>
    /// Serializes the metadata to JSON.
    /// </summary>
    public string GetSerializedMetadata()
    {
        // return a dictionary from the metadata without the text, document_Id, and source_Id properties

        if (this.Metadata is null)
        {
            return string.Empty;
        }

        var propertiesToSkip = new HashSet<string>() { "text", "document_Id", "source_Id", "created_at" };

        var distinctMetadata = this.Metadata
            .Where(x => !propertiesToSkip.Contains(x.Key))
            .ToDictionary(x => x.Key, x => x.Value);

        return JsonSerializer.Serialize(distinctMetadata, JsonOptionsCache.Default);
    }

    internal UpdateVectorRequest ToUpdateRequest()
    {
        return UpdateVectorRequest.FromPineconeDocument(this);
    }
}

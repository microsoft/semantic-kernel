// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Data;

namespace VectorStoreRAG;

/// <summary>
/// Data model for storing a section of text with an embedding and an optional reference link.
/// </summary>
/// <typeparam name="TKey">The type of the data model key.</typeparam>
internal sealed class TextSnippet<TKey>
{
    [VectorStoreRecordKey]
    public required TKey Key { get; set; }

    [TextSearchResultValue]
    [VectorStoreRecordData]
    public string? Text { get; set; }

    [TextSearchResultName]
    [VectorStoreRecordData]
    public string? ReferenceDescription { get; set; }

    [TextSearchResultLink]
    [VectorStoreRecordData]
    public string? ReferenceLink { get; set; }

    /// <summary>
    /// The text embedding for this snippet. This is used to search the vector store.
    /// While this is a string property it has the vector attribute, which means whatever
    /// text it contains will be converted to a vector and stored as a vector in the vector store.
    /// </summary>
    [VectorStoreRecordVector(1536)]
    public string? TextEmbedding => this.Text;
}

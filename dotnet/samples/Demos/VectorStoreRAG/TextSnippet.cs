// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace VectorStoreRAG;

/// <summary>
/// Data model for storing a section of text with an embedding and an optional reference link.
/// </summary>
/// <typeparam name="TKey">The type of the data model key.</typeparam>
internal sealed class TextSnippet<TKey>
{
    [VectorStoreKeyProperty]
    public required TKey Key { get; set; }

    [VectorStoreDataProperty]
    public string? Text { get; set; }

    [VectorStoreDataProperty]
    public string? ReferenceDescription { get; set; }

    [VectorStoreDataProperty]
    public string? ReferenceLink { get; set; }

    [VectorStoreVectorProperty(1536)]
    public ReadOnlyMemory<float> TextEmbedding { get; set; }
}

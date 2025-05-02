// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace VectorStoreRAG;

/// <summary>
/// Data model for storing a section of text with an embedding and an optional reference link.
/// </summary>
/// <typeparam name="TKey">The type of the data model key.</typeparam>
internal sealed class TextSnippet<TKey>
{
    [VectorStoreKey]
    public required TKey Key { get; set; }

    [VectorStoreData]
    public string? Text { get; set; }

    [VectorStoreData]
    public string? ReferenceDescription { get; set; }

    [VectorStoreData]
    public string? ReferenceLink { get; set; }

    [VectorStoreVector(1536)]
    public ReadOnlyMemory<float> TextEmbedding { get; set; }
}

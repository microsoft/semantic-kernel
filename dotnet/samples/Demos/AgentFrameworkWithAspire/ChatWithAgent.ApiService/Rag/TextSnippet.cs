// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Data;

namespace ChatWithAgent.ApiService;

/// <summary>
/// Data model for storing a section of text with an embedding and an optional reference link.
/// </summary>
/// <typeparam name="TKey">The type of the data model key.</typeparam>
internal sealed class TextSnippet<TKey>
{
    [VectorStoreKey]
    [JsonPropertyName("chunk_id")]
    public required TKey Key { get; set; }

    [VectorStoreData]
    [JsonPropertyName("chunk")]
    [TextSearchResultValue]
    public string? Text { get; set; }

    [VectorStoreData]
    [JsonPropertyName("title")]
    [TextSearchResultName]
    [TextSearchResultLink]
    public string? Reference { get; set; }

    [VectorStoreVector(1536)]
    [JsonPropertyName("text_vector")]
    public ReadOnlyMemory<float> TextEmbedding { get; set; }
}

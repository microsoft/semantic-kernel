// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

[JsonDerivedType(typeof(TextChunk))]
[JsonDerivedType(typeof(ImageUrlChunk))]
[JsonDerivedType(typeof(DocumentUrlChunk))]
internal abstract class ContentChunk(ContentChunkType type)
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = type.ToString();
}

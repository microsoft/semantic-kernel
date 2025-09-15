// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

internal class DocumentUrlChunk(string documentUrl) : ContentChunk(ContentChunkType.DocumentUrl)
{
    [JsonPropertyName("document_url")]
    public string DocumentUrl { get; set; } = documentUrl;
}

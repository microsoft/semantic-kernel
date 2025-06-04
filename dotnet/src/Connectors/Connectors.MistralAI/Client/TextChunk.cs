// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;
internal class TextChunk(string text) : ContentChunk(ContentChunkType.Text)
{
    [JsonPropertyName("text")]
    public string Text { get; set; } = text;
}

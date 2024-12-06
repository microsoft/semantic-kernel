// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;
internal class ImageUrlChunk(Uri imageUrl) : ContentChunk(ContentChunkType.ImageUrl)
{
    [JsonPropertyName("image_url")]
    public string ImageUrl { get; set; } = imageUrl.ToString();
}

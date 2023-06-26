// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextEmbedding;

namespace Microsoft.SemanticKernel.Text;

[JsonSerializable(typeof(Dictionary<string, int>))]
[JsonSerializable(typeof(ImageGenerationRequest))]
[JsonSerializable(typeof(ImageGenerationResponse))]
[JsonSerializable(typeof(AzureImageGenerationResponse))]
[JsonSerializable(typeof(JsonNode))]
[JsonSerializable(typeof(TextEmbeddingResponse))]
internal sealed partial class SourceGenerationContext : JsonSerializerContext
{
    public static readonly SourceGenerationContext WithGeneralOptions = new(new JsonSerializerOptions(Json.GeneralOptions));
}

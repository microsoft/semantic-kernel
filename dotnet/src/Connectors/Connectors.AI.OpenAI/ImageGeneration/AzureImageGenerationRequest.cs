// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;

public class AzureImageGenerationRequest
{
    [JsonPropertyName("caption")]
    public string Caption { get; set; } = string.Empty;
    [JsonPropertyName("resolution")]
    public string Resolution { get; set; } = "256x256";
}

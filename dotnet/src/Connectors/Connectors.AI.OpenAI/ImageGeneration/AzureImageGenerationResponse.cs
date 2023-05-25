// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;

public class AzureImageGenerationResponse
{
    public class AzureImageGenerationResult
    {
        [JsonPropertyName("caption")]
        public string Caption { get; set; } = string.Empty;
        [JsonPropertyName("contentUrl")]
        [SuppressMessage("Design", "CA1056:URI return values should not be strings", Justification = "Using the original value")]
        public string ContentUrl { get; set; } = string.Empty;
        [JsonPropertyName("ContentUrlExpiresAt")]
        public DateTime ContentUrlExpiresAt { get; set; }
        [JsonPropertyName("createdDateTime")]
        public DateTime CreatedDateTime { get; set; }
    }
    [JsonPropertyName("result")]
    public AzureImageGenerationResult? Result { get; set; }
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;
    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;
}

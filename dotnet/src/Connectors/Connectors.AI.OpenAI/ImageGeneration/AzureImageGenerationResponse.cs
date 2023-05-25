// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;

/// <summary>
/// Image generation response
/// </summary>
public class AzureImageGenerationResponse
{
    /// <summary>
    /// Azure OpenAI Image response
    /// </summary>
    public sealed class AzureImageGenerationResult
    {
        /// <summary>
        /// Image Description
        /// </summary>
        [JsonPropertyName("caption")]
        public string Caption { get; set; } = string.Empty;
        /// <summary>
        /// URL to the image created
        /// </summary>
        [JsonPropertyName("contentUrl")]
        [SuppressMessage("Design", "CA1056:URI return values should not be strings", Justification = "Using the original value")]
        public string ContentUrl { get; set; } = string.Empty;
        /// <summary>
        /// Expiration time of the URL
        /// </summary>
        [JsonPropertyName("ContentUrlExpiresAt")]
        public DateTime ContentUrlExpiresAt { get; set; }
        /// <summary>
        /// Creation time
        /// </summary>
        [JsonPropertyName("createdDateTime")]
        public DateTime CreatedDateTime { get; set; }
    }
    /// <summary>
    /// Image generation result
    /// </summary>
    [JsonPropertyName("result")]
    public AzureImageGenerationResult? Result { get; set; }
    /// <summary>
    /// Request Id
    /// </summary>
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;
    /// <summary>
    /// Request Status
    /// </summary>
    [JsonPropertyName("status")]
    public string Status { get; set; } = string.Empty;
}

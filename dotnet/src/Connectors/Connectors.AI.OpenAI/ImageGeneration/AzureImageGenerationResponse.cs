// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;

/// <summary>
/// Image generation response
/// </summary>
public class AzureImageGenerationResponse
{
    /// <summary>
    /// Image generation result
    /// </summary>
    [JsonPropertyName("result")]
    public ImageGenerationResponse? Result { get; set; }

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

    /// <summary>
    ///  Creation time
    /// </summary>
    [JsonPropertyName("created")]
    public int Created { get; set; }

    /// <summary>
    /// Expiration time of the URL
    /// </summary>
    [JsonPropertyName("expires")]
    public int Expires { get; set; }
}

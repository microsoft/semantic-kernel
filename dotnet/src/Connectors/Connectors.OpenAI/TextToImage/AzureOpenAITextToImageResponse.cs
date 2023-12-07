// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Text to image response
/// </summary>
[Experimental("SKEXP0012")]
public class AzureOpenAITextToImageResponse
{
    /// <summary>
    /// Text to image result
    /// </summary>
    [JsonPropertyName("result")]
    public TextToImageResponse? Result { get; set; }

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

// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// The Amazon Titan Text Generation Request object.
/// </summary>
internal sealed class TitanEmbedRequest
{
    /// <summary>
    /// The provided input text string for text embedding response.
    /// </summary>
    [JsonPropertyName("inputText")]
    public string? InputText { get; set; }
}

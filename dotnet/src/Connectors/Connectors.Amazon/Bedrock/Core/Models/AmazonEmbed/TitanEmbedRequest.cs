// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

internal sealed class TitanEmbedRequest
{
    [JsonPropertyName("inputText")]
    public string InputText { get; set; }
    [JsonPropertyName("dimensions")]
    public int Dimensions { get; set; }
    [JsonPropertyName("normalize")]
    public bool Normalize { get; set; }
}

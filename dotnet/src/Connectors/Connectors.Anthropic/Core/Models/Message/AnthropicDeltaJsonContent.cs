// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

internal sealed class AnthropicDeltaJsonContent : AnthropicContent
{
    /// <summary>
    /// Only used when type is "input_json_delta". The partial json content.
    /// </summary>
    [JsonRequired]
    [JsonPropertyName("partial_json")]
    public string PartialJson { get; set; }
}

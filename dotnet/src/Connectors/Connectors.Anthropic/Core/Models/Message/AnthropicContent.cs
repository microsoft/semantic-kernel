// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

/// <summary>
/// Represents the request/response content of Anthropic.
/// </summary>
[InternalJsonDerived(typeof(AnthropicTextContent), typeDiscriminator: "text")]
[InternalJsonDerived(typeof(AnthropicImageContent), typeDiscriminator: "image")]
internal abstract class AnthropicContent
{
    [JsonConstructor]
    internal protected AnthropicContent(string type)
    {
        this.Type = type;
    }
    /// <summary>
    /// Currently supported only base64.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; set; }
}

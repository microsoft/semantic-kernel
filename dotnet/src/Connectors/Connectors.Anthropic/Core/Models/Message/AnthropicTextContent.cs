// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

internal sealed class AnthropicTextContent : AnthropicContent
{
    /// <summary>
    /// Only used when type is "text". The text content.
    /// </summary>
    [JsonRequired]
    [JsonPropertyName("text")]
    public string Text { get; set; } = null!;
}

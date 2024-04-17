// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

internal sealed class AnthropicToolResultContent : AnthropicContent
{
    [JsonPropertyName("tool_use_id")]
    [JsonRequired]
    public string ToolId { get; set; } = null!;

    [JsonPropertyName("content")]
    [JsonRequired]
    public AnthropicContent Content { get; set; } = null!;

    [JsonPropertyName("is_error")]
    public bool IsError { get; set; }
}

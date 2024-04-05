// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Nodes;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Anthropic.Core;

internal sealed class ClaudeToolResultContent : ClaudeMessageContent
{
    [JsonPropertyName("tool_use_id")]
    [JsonRequired]
    public string ToolId { get; set; } = null!;

    /// <summary>
    /// Optional. The function parameters and values in JSON object format.
    /// </summary>
    [JsonPropertyName("content")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public JsonNode? Arguments { get; set; }

    [JsonPropertyName("is_error")]
    public bool IsError { get; set; }
}

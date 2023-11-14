// Copyright (c) Microsoft. All rights reserved.
#pragma warning disable CA1812
#pragma warning disable CA1852

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Models;

internal class ToolResultModel
{
    private static readonly object s_placeholder = new();

    /// <summary>
    /// The tool call identifier.
    /// </summary>
    [JsonPropertyName("tool_call_id")]
    public string CallId { get; set; } = string.Empty;

    /// <summary>
    /// The tool output
    /// </summary>
    [JsonPropertyName("output")]
    public object Output { get; set; } = s_placeholder;
}

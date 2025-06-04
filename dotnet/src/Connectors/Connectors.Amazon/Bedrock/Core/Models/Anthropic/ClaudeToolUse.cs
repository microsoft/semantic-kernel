// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Amazon.BedrockRuntime.Model;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Anthropic Claude request object.
/// </summary>
internal static class ClaudeToolUse
{
    /// <summary>
    /// (Optional) Definitions of tools that the model may use.
    /// </summary>
    internal sealed class ClaudeTool : Tool
    {
        /// <summary>
        /// The name of the tool.
        /// </summary>
        [JsonPropertyName("name")]
        public string? Name { get; set; }

        /// <summary>
        /// (optional, but strongly recommended) The description of the tool.
        /// </summary>
        [JsonPropertyName("description")]
        public string? Description { get; set; }

        /// <summary>
        /// The JSON schema for the tool.
        /// </summary>
        [JsonPropertyName("input_schema")]
        public string? InputSchema { get; set; }
    }

    /// <summary>
    /// (Optional) Specifies how the model should use the provided tools. The model can use a specific tool, any available tool, or decide by itself.
    /// </summary>
    internal sealed class ClaudeToolChoice
    {
        /// <summary>
        /// The type of tool choice. Possible values are any (use any available tool), auto (the model decides), and tool (use the specified tool).
        /// </summary>
        [JsonPropertyName("type")]
        public string? Type { get; set; }

        /// <summary>
        /// (Optional) The name of the tool to use. Required if you specify tool in the type field.
        /// </summary>
        [JsonPropertyName("name")]
        public string? Name { get; set; }
    }
}

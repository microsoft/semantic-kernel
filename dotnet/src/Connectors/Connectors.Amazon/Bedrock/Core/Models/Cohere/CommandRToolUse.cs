// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Connectors.Amazon.Core;

/// <summary>
/// Cohere Command R Text Generation Request object for Invoke Model Bedrock API call.
/// </summary>
internal static class CommandRToolUse
{
    /// <summary>
    /// Tool parameters.
    /// </summary>
    [Serializable]
    internal sealed class Tool
    {
        /// <summary>
        /// Name of the tool.
        /// </summary>
        [JsonPropertyName("name")]
        public required string Name { get; set; }
        /// <summary>
        /// Description of the tool.
        /// </summary>
        [JsonPropertyName("description")]
        public required string Description { get; set; }
        /// <summary>
        /// Definitions for each tool.
        /// </summary>
        [JsonPropertyName("parameter_definitions")]
        public required Dictionary<string, ToolParameter> ParameterDefinitions { get; set; }
    }
    /// <summary>
    /// Components of each tool parameter.
    /// </summary>
    [Serializable]
    internal sealed class ToolParameter
    {
        /// <summary>
        /// Description of parameter.
        /// </summary>
        [JsonPropertyName("description")]
        public required string Description { get; set; }
        /// <summary>
        /// Parameter type (str, int, etc.) as described in a string.
        /// </summary>
        [JsonPropertyName("type")]
        public required string Type { get; set; }
        /// <summary>
        /// Whether this parameter is required.
        /// </summary>
        [JsonPropertyName("required")]
        public required bool Required { get; set; }
    }
    /// <summary>
    /// Cohere tool result.
    /// </summary>
    [Serializable]
    internal sealed class ToolResult
    {
        /// <summary>
        /// The tool call.
        /// </summary>
        [JsonPropertyName("call")]
        public ToolCall? Call { get; set; }
        /// <summary>
        /// Outputs from the tool call.
        /// </summary>
        [JsonPropertyName("outputs")]
        public static List<Dictionary<string, string>>? Outputs { get; set; }
    }
    /// <summary>
    /// Tool call object to be passed into the tool call.
    /// </summary>
    [Serializable]
    internal sealed class ToolCall
    {
        /// <summary>
        /// Name of tool.
        /// </summary>
        [JsonPropertyName("name")]
        public string? Name { get; set; }
        /// <summary>
        /// Parameters for the tool.
        /// </summary>
        [JsonPropertyName("parameters")]
        public Dictionary<string, string>? Parameters { get; set; }
    }
}

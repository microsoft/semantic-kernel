// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Experimental.Agents.Models;

/// <summary>
/// Tool entry
/// </summary>
internal sealed record ToolModel
{
    /// <summary>
    /// Type of tool to have at agent's disposition
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; init; } = string.Empty;

    /// <summary>
    /// The function definition for Type = 'function'.
    /// </summary>
    [JsonPropertyName("function")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public FunctionModel? Function { get; init; }

    /// <summary>
    /// Defines the function when ToolModel.Type == 'function'.
    /// </summary>
    public sealed record FunctionModel
    {
        /// <summary>
        /// The function name.
        /// </summary>
        [JsonPropertyName("name")]
        public string Name { get; init; } = string.Empty;

        /// <summary>
        /// The function description.
        /// </summary>
        [JsonPropertyName("description")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? Description { get; init; }

        /// <summary>
        /// The function description.
        /// </summary>
        [JsonPropertyName("parameters")]
        public OpenAIParameters Parameters { get; init; } = OpenAIParameters.Empty;
    }
}

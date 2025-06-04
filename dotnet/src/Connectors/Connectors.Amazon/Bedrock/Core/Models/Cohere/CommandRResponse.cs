// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Cohere Command R Text Generation Response body.
/// </summary>
internal sealed class CommandRResponse
{
    /// <summary>
    /// Unique identifier for chat completion
    /// </summary>
    [JsonPropertyName("response_id")]
    public string? ResponseId { get; set; }

    /// <summary>
    /// The model’s response to chat message input.
    /// </summary>
    [JsonPropertyName("text")]
    public string? Text { get; set; }

    /// <summary>
    /// Unique identifier for chat completion, used with Feedback endpoint on Cohere’s platform.
    /// </summary>
    [JsonPropertyName("generation_id")]
    public string? GenerationId { get; set; }

    /// <summary>
    /// An array of inline citations and associated metadata for the generated reply.
    /// </summary>
    [JsonPropertyName("citations")]
    public List<Citation>? Citations { get; set; }

    /// <summary>
    /// The full prompt that was sent to the model. Specify the return_prompt field to return this field.
    /// </summary>
    [JsonPropertyName("prompt")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Prompt { get; set; }

    /// <summary>
    /// The reason why the model stopped generating output.
    /// </summary>
    [JsonPropertyName("finish_reason")]
    public string? FinishReason { get; set; }

    /// <summary>
    /// A list of appropriate tools to calls. Only returned if you specify the tools input field.
    /// </summary>
    [JsonPropertyName("tool_calls")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<ToolCall>? ToolCalls { get; set; }

    /// <summary>
    /// API usage data (only exists for streaming).
    /// </summary>
    [JsonPropertyName("meta")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public MetaCommandR? Meta { get; set; }

    /// <summary>
    /// Citation object for array of inline citations and associated metadata for the generated reply.
    /// </summary>
    internal sealed class Citation
    {
        /// <summary>
        /// The index that the citation begins at, starting from 0.
        /// </summary>
        [JsonPropertyName("start")]
        public int Start { get; set; }

        /// <summary>
        /// The index that the citation ends after, starting from 0.
        /// </summary>
        [JsonPropertyName("end")]
        public int End { get; set; }

        /// <summary>
        /// The text that the citation pertains to.
        /// </summary>
        [JsonPropertyName("text")]
        public string? Text { get; set; }

        /// <summary>
        /// An array of document IDs that correspond to documents that are cited for the text.
        /// </summary>
        [JsonPropertyName("document_ids")]
        public List<string>? DocumentIds { get; set; }
    }

    /// <summary>
    /// Components for tool calling.
    /// </summary>
    internal sealed class ToolCall
    {
        /// <summary>
        /// Name of tool.
        /// </summary>
        [JsonPropertyName("name")]
        public string? Name { get; set; }

        /// <summary>
        /// Parameters for tool.
        /// </summary>
        [JsonPropertyName("parameters")]
        public Dictionary<string, string>? Parameters { get; set; }
    }

    /// <summary>
    /// API usage data (only exists for streaming).
    /// </summary>
    internal sealed class MetaCommandR
    {
        /// <summary>
        /// The API version. The version is in the version field.
        /// </summary>
        [JsonPropertyName("api_version")]
        public ApiVersion? ApiVersion { get; set; }

        /// <summary>
        /// The billed units.
        /// </summary>
        [JsonPropertyName("billed_units")]
        public BilledUnits? BilledUnits { get; set; }
    }

    /// <summary>
    /// The API version.
    /// </summary>
    internal sealed class ApiVersion
    {
        /// <summary>
        /// The corresponding version field for the API version identification.
        /// </summary>
        [JsonPropertyName("version")]
        public string? Version { get; set; }
    }

    /// <summary>
    /// The billed units.
    /// </summary>
    internal sealed class BilledUnits
    {
        /// <summary>
        /// The number of input tokens that were billed.
        /// </summary>
        [JsonPropertyName("input_tokens")]
        public int InputTokens { get; set; }

        /// <summary>
        /// The number of output tokens that were billed.
        /// </summary>
        [JsonPropertyName("output_tokens")]
        public int OutputTokens { get; set; }
    }
}

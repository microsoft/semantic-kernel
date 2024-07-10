// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Connectors.Amazon.Core.Requests;

namespace Connectors.Amazon.Models.Cohere;

public class CommandRTextRequest
{
    public class CommandRTextGenerationRequest : ITextGenerationRequest
    {
        [JsonPropertyName("message")]
        public required string Message { get; set; }

        [JsonPropertyName("chat_history")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<ChatMessage>? ChatHistory { get; set; }

        [JsonPropertyName("documents")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<Document>? Documents { get; set; }

        [JsonPropertyName("search_queries_only")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? SearchQueriesOnly { get; set; }

        [JsonPropertyName("preamble")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? Preamble { get; set; }

        [JsonPropertyName("max_tokens")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxTokens { get; set; }

        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? Temperature { get; set; }

        [JsonPropertyName("p")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? TopP { get; set; }

        [JsonPropertyName("k")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? TopK { get; set; }

        [JsonPropertyName("prompt_truncation")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? PromptTruncation { get; set; }

        [JsonPropertyName("frequency_penalty")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? FrequencyPenalty { get; set; }

        [JsonPropertyName("presence_penalty")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? PresencePenalty { get; set; }

        [JsonPropertyName("seed")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? Seed { get; set; }

        [JsonPropertyName("return_prompt")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ReturnPrompt { get; set; }

        [JsonPropertyName("tools")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<Tool>? Tools { get; set; }

        [JsonPropertyName("tool_results")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<ToolResult>? ToolResults { get; set; }

        [JsonPropertyName("stop_sequences")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<string>? StopSequences { get; set; }

        [JsonPropertyName("raw_prompting")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? RawPrompting { get; set; }

        string ITextGenerationRequest.InputText => Message;

        double? ITextGenerationRequest.TopP => TopP;

        double? ITextGenerationRequest.Temperature => Temperature;

        int? ITextGenerationRequest.MaxTokens => MaxTokens;

        IList<string>? ITextGenerationRequest.StopSequences => StopSequences;
    }

    [Serializable]
    public class ChatMessage
    {
        [JsonPropertyName("role")]
        public required string Role { get; set; }

        [JsonPropertyName("message")]
        public required string Message { get; set; }
    }

    [Serializable]
    public class Document
    {
        [JsonPropertyName("title")]
        public required string Title { get; set; }

        [JsonPropertyName("snippet")]
        public required string Snippet { get; set; }
    }

    [Serializable]
    public class Tool
    {
        [JsonPropertyName("name")]
        public required string Name { get; set; }

        [JsonPropertyName("description")]
        public required string Description { get; set; }

        [JsonPropertyName("parameter_definitions")]
        public required Dictionary<string, ToolParameter> ParameterDefinitions { get; set; }
    }

    [Serializable]
    public class ToolParameter
    {
        [JsonPropertyName("description")]
        public required string Description { get; set; }

        [JsonPropertyName("type")]
        public required string Type { get; set; }

        [JsonPropertyName("required")]
        public required bool Required { get; set; }
    }

    [Serializable]
    public class ToolResult
    {
        [JsonPropertyName("call")]
        public required ToolCall Call { get; set; }

        [JsonPropertyName("outputs")]
        public required IList<Dictionary<string, object>> Outputs { get; set; }
    }

    [Serializable]
    public class ToolCall
    {
        [JsonPropertyName("name")]
        public required string Name { get; set; }

        [JsonPropertyName("parameters")]
        public required Dictionary<string, string> Parameters { get; set; }
    }
}

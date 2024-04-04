// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Client.Models;

internal sealed class ChatCompletionResponse
{
    [JsonPropertyName("id")]
    public string? Id { get; set; }

    [JsonPropertyName("object")]
    public string? Object { get; set; }

    [JsonPropertyName("created")]
    public long Created { get; set; }

    [JsonPropertyName("model")]
    public string? Model { get; set; }

    [JsonPropertyName("system_fingerprint")]
    public string? SystemFingerprint { get; set; }

    [JsonPropertyName("choices")]
    public List<ChatCompletionChoice>? Choices { get; set; }

    [JsonPropertyName("usage")]
    public ChatCompletionUsage? Usage { get; set; }

    internal sealed class ChatCompletionChoice
    {
        [JsonPropertyName("logprobs")]
        public ChatCompletionChoiceLogProbs? LogProbs { get; set; }

        [JsonPropertyName("finish_reason")]
        public string? FinishReason { get; set; }

        [JsonPropertyName("index")]
        public int Index { get; set; }

        [JsonPropertyName("message")]
        public ChatCompletionMessage? Message { get; set; }
    }

    internal sealed class ChatCompletionMessage
    {
        [JsonPropertyName("content")]
        public string? Content { get; set; }

        [JsonPropertyName("tool_calls")]
        public List<ChatCompletionChoiceToolCall>? ToolCalls { get; set; }

        [JsonPropertyName("function_call")]
        public ChatCompletionChoiceToolCallFunction? FunctionCall { get; set; }

        [JsonPropertyName("role")]
        public string? Role { get; set; }

        [JsonPropertyName("name")]
        public string? Name { get; set; }
    }

    internal sealed class ChatCompletionChoiceToolCall
    {
        [JsonPropertyName("index")]
        public int Index { get; set; }

        [JsonPropertyName("id")]
        public string? Id { get; set; }

        [JsonPropertyName("type")]
        public string? Type { get; set; }

        [JsonPropertyName("function")]
        public ChatCompletionChoiceToolCallFunction? Function { get; set; }
    }

    internal sealed class ChatCompletionChoiceToolCallFunction
    {
        [JsonPropertyName("name")]
        public string? Name { get; set; }

        [JsonPropertyName("arguments")]
        public string? Arguments { get; set; }
    }

    internal sealed class ChatCompletionChoiceLogProbs
    {
        public List<ChatCompletionChoiceLogProbsContent>? Content { get; set; }
    }

    internal sealed class ChatCompletionChoiceLogProbsContent
    {
        [JsonPropertyName("token")]
        public string? Token { get; set; }

        [JsonPropertyName("logprob")]
        public float LogProb { get; set; }

        [JsonPropertyName("bytes")]
        public int[]? Bytes { get; set; }

        [JsonPropertyName("top_logprobs")]
        public List<ChatCompletionChoiceTopLogProb>? TopLogProbs { get; set; }
    }

    internal sealed class ChatCompletionChoiceTopLogProb
    {
        [JsonPropertyName("token")]
        public string? Token { get; set; }

        [JsonPropertyName("logprob")]
        public float LogProb { get; set; }

        [JsonPropertyName("bytes")]
        public int[]? Bytes { get; set; }
    }

    internal sealed class ChatCompletionUsage
    {
        [JsonPropertyName("prompt_tokens")]
        public int PromptTokens { get; set; }

        [JsonPropertyName("completion_tokens")]
        public int CompletionTokens { get; set; }

        [JsonPropertyName("total_tokens")]
        public int TotalTokens { get; set; }
    }
}

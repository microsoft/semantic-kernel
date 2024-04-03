// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Client;

internal sealed class ChatCompletionStreamResponse
{
    [JsonPropertyName("id")]
    public int Id { get; set; }

    [JsonPropertyName("object")]
    public string? Object { get; set; }

    [JsonPropertyName("created")]
    public long Created { get; set; }

    [JsonPropertyName("model")]
    public string? Model { get; set; }

    [JsonPropertyName("system_fingerprint")]
    public string? SystemFingerprint { get; set; }

    [JsonPropertyName("choices")]
    public List<ChatCompletionStreamChoice>? Choices { get; set; }

    internal sealed class ChatCompletionStreamChoice
    {
        [JsonPropertyName("delta")]
        public ChatCompletionStreamChoiceDelta? Delta { get; set; }

        [JsonPropertyName("logprobs")]
        public ChatCompletionStreamChoiceLogProbs? LogProbs { get; set; }

        [JsonPropertyName("finish_reason")]
        public string? FinishReason { get; set; }

        [JsonPropertyName("index")]
        public int Index { get; set; }
    }

    internal sealed class ChatCompletionStreamChoiceDelta
    {
        [JsonPropertyName("content")]
        public string? Content { get; set; }

        [JsonPropertyName("tool_calls")]
        public List<ChatCompletionStreamChoiceDeltaToolCall>? ToolCalls { get; set; }

        [JsonPropertyName("function_call")]
        public ChatCompletionStreamChoiceDeltaToolCallFunction? FunctionCall { get; set; }

        [JsonPropertyName("role")]
        public string? Role { get; set; }
    }

    internal sealed class ChatCompletionStreamChoiceDeltaToolCall
    {
        [JsonPropertyName("index")]
        public int Index { get; set; }

        [JsonPropertyName("id")]
        public string? Id { get; set; }

        [JsonPropertyName("type")]
        public string? Type { get; set; }

        [JsonPropertyName("function")]
        public ChatCompletionStreamChoiceDeltaToolCallFunction? Function { get; set; }
    }

    internal sealed class ChatCompletionStreamChoiceDeltaToolCallFunction
    {
        [JsonPropertyName("name")]
        public string? Name { get; set; }

        [JsonPropertyName("arguments")]
        public string? Arguments { get; set; }
    }

    internal sealed class ChatCompletionStreamChoiceLogProbs
    {
        public List<ChatCompletionStreamChoiceLogProbsContent>? Content { get; set; }
    }

    internal sealed class ChatCompletionStreamChoiceLogProbsContent
    {
        [JsonPropertyName("token")]
        public string? Token { get; set; }

        [JsonPropertyName("logprob")]
        public float LogProb { get; set; }

        [JsonPropertyName("bytes")]
        public int[]? Bytes { get; set; }

        [JsonPropertyName("top_logprobs")]
        public List<ChatCompletionStreamChoiceTopLogProb>? TopLogProbs { get; set; }
    }

    internal sealed class ChatCompletionStreamChoiceTopLogProb
    {
        [JsonPropertyName("token")]
        public string? Token { get; set; }

        [JsonPropertyName("logprob")]
        public float LogProb { get; set; }

        [JsonPropertyName("bytes")]
        public int[]? Bytes { get; set; }
    }
}

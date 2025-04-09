// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

internal sealed class ChatCompletionStreamResponse
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
    public List<Choice>? Choices { get; set; }

    internal sealed class Choice
    {
        [JsonPropertyName("delta")]
        public ChoiceDelta? Delta { get; set; }

        [JsonPropertyName("logprobs")]
        public ChoiceLogProbs? LogProbs { get; set; }

        [JsonPropertyName("finish_reason")]
        public string? FinishReason { get; set; }

        [JsonPropertyName("index")]
        public int Index { get; set; }
    }

    internal sealed class ChoiceDelta
    {
        [JsonPropertyName("content")]
        public string? Content { get; set; }

        [JsonPropertyName("tool_calls")]
        public List<ChoiceDeltaToolCall>? ToolCalls { get; set; }

        [JsonPropertyName("function_call")]
        public ChoiceDeltaToolCallFunction? FunctionCall { get; set; }

        [JsonPropertyName("role")]
        public string? Role { get; set; }
    }

    internal sealed class ChoiceDeltaToolCall
    {
        [JsonPropertyName("index")]
        public int Index { get; set; }

        [JsonPropertyName("id")]
        public string? Id { get; set; }

        [JsonPropertyName("type")]
        public string? Type { get; set; }

        [JsonPropertyName("function")]
        public ChoiceDeltaToolCallFunction? Function { get; set; }
    }

    internal sealed class ChoiceDeltaToolCallFunction
    {
        [JsonPropertyName("name")]
        public string? Name { get; set; }

        [JsonPropertyName("arguments")]
        public string? Arguments { get; set; }
    }

    internal sealed class ChoiceLogProbs
    {
        [JsonPropertyName("content")]
        public List<ChoiceLogProbsContent>? Content { get; set; }
    }

    internal sealed class ChoiceLogProbsContent
    {
        [JsonPropertyName("token")]
        public string? Token { get; set; }

        [JsonPropertyName("logprob")]
        public double LogProb { get; set; }

        [JsonPropertyName("bytes")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int[]? Bytes { get; set; }

        [JsonPropertyName("top_logprobs")]
        public List<ChoiceTopLogProb>? TopLogProbs { get; set; }
    }

    internal sealed class ChoiceTopLogProb
    {
        [JsonPropertyName("token")]
        public string? Token { get; set; }

        [JsonPropertyName("logprob")]
        public double LogProb { get; set; }

        [JsonPropertyName("bytes")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int[]? Bytes { get; set; }
    }
}

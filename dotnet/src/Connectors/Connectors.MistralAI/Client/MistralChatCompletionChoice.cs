// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// Mistral chat completion choice.
/// </summary>
internal class MistralChatCompletionChoice
{
    [JsonPropertyName("finish_reason")]
    public string? FinishReason { get; set; }

    [JsonPropertyName("index")]
    public int? Index { get; set; }

    [JsonPropertyName("delta")]
    public MistralChatMessage? Delta { get; set; }

    [JsonPropertyName("logprobs")]
    public string? LogProbs { get; set; }
}

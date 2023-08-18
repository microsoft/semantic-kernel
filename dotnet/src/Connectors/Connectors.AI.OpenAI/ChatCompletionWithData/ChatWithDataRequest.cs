// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

[Serializable]
internal sealed class ChatWithDataRequest
{
    [JsonPropertyName("temperature")]
    public double Temperature { get; set; } = 0;

    [JsonPropertyName("top_p")]
    public double TopP { get; set; } = 0;

    [JsonPropertyName("stream")]
    public bool IsStreamEnabled { get; set; }

    [JsonPropertyName("stop")]
    public IList<string> StopSequences { get; set; } = Array.Empty<string>();

    [JsonPropertyName("max_tokens")]
    public int? MaxTokens { get; set; }

    [JsonPropertyName("presence_penalty")]
    public double PresencePenalty { get; set; } = 0;

    [JsonPropertyName("frequency_penalty")]
    public double FrequencyPenalty { get; set; } = 0;

    [JsonPropertyName("logit_bias")]
    public IDictionary<int, int> TokenSelectionBiases { get; set; } = new Dictionary<int, int>();

    [JsonPropertyName("dataSources")]
    public IList<ChatWithDataSource> DataSources { get; set; } = Array.Empty<ChatWithDataSource>();

    [JsonPropertyName("messages")]
    public IList<ChatWithDataMessage> Messages { get; set; } = Array.Empty<ChatWithDataMessage>();
}

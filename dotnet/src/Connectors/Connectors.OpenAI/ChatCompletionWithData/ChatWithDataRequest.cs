// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

[Experimental("SKEXP0010")]
internal sealed class ChatWithDataRequest
{
    [JsonPropertyName("temperature")]
    public double Temperature { get; set; } = 0;

    [JsonPropertyName("top_p")]
    public double TopP { get; set; } = 0;

    [JsonPropertyName("stream")]
    public bool IsStreamEnabled { get; set; }

    [JsonPropertyName("stop")]
    public IList<string>? StopSequences { get; set; } = Array.Empty<string>();

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

[Experimental("SKEXP0010")]
internal sealed class ChatWithDataSource
{
    [JsonPropertyName("type")]
    // The current API only supports "AzureCognitiveSearch" as name otherwise an error is returned.
    // Validation error at #/dataSources/0: Input tag 'AzureAISearch' found using 'type' does not match any of
    // the expected tags: 'AzureCognitiveSearch', 'Elasticsearch', 'AzureCosmosDB', 'Pinecone', 'AzureMLIndex', 'Microsoft365'
    public string Type { get; set; } = "AzureCognitiveSearch";

    [JsonPropertyName("parameters")]
    public ChatWithDataSourceParameters Parameters { get; set; } = new ChatWithDataSourceParameters();
}

[Experimental("SKEXP0010")]
internal sealed class ChatWithDataSourceParameters
{
    [JsonPropertyName("endpoint")]
    public string Endpoint { get; set; } = string.Empty;

    [JsonPropertyName("key")]
    public string ApiKey { get; set; } = string.Empty;

    [JsonPropertyName("indexName")]
    public string IndexName { get; set; } = string.Empty;
}

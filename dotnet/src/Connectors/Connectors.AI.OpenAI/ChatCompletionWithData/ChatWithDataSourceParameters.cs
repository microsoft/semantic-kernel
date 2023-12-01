// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

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

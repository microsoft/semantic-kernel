// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

[Serializable]
internal sealed class ChatWithDataSource
{
    [JsonPropertyName("type")]
    public string Type { get; set; } = ChatWithDataSourceType.AzureCognitiveSearch.ToString();

    [JsonPropertyName("parameters")]
    public ChatWithDataSourceParameters Parameters { get; set; } = new ChatWithDataSourceParameters();
}

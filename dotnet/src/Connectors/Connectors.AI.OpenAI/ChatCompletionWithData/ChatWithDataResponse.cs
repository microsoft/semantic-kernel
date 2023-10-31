// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes

[Serializable]
internal sealed class ChatWithDataResponse
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("created")]
    public int Created { get; set; } = default;

    [JsonPropertyName("choices")]
    public IList<ChatWithDataChoice> Choices { get; set; } = Array.Empty<ChatWithDataChoice>();
}

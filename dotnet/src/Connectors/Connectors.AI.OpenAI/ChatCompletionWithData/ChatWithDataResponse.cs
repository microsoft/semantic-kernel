// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

[Serializable]
[SuppressMessage("Performance", "CA1812:Avoid uninstantiated internal classes", Justification = "Used for JSON deserialization")]
internal sealed class ChatWithDataResponse
{
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    [JsonPropertyName("created")]
    public int Created { get; set; } = default;

    [JsonPropertyName("choices")]
    public IList<ChatWithDataChoice> Choices { get; set; } = Array.Empty<ChatWithDataChoice>();
}

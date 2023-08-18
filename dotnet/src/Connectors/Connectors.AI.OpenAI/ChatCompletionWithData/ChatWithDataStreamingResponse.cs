// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

[Serializable]
[SuppressMessage("Performance", "CA1812:Avoid uninstantiated internal classes", Justification = "Used for JSON deserialization")]
internal sealed class ChatWithDataStreamingResponse
{
    [JsonPropertyName("choices")]
    public IList<ChatWithDataStreamingChoice> Choices { get; set; } = Array.Empty<ChatWithDataStreamingChoice>();
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

[SuppressMessage("Performance", "CA1812:Avoid uninstantiated internal classes", Justification = "Used for JSON deserialization")]
internal sealed class ChatWithDataStreamingChoice
{
    [JsonPropertyName("messages")]
    public IList<ChatWithDataStreamingMessage> Messages { get; set; } = Array.Empty<ChatWithDataStreamingMessage>();

    [JsonPropertyName("index")]
    public int Index { get; set; } = 0;
}

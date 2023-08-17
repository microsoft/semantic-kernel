// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

internal class ChatWithDataStreamingChoice
{
    [JsonPropertyName("messages")]
    public IList<ChatWithDataStreamingMessage> Messages { get; set; } = Array.Empty<ChatWithDataStreamingMessage>();
}

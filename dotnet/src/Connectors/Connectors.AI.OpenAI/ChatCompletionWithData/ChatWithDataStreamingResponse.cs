// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

internal class ChatWithDataStreamingResponse
{
    [JsonPropertyName("choices")]
    public IList<ChatWithDataStreamingChoice> Choices { get; set; } = Array.Empty<ChatWithDataStreamingChoice>();
}

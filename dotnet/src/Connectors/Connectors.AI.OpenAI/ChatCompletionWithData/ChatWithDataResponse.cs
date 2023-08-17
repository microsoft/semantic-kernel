// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

[Serializable]
internal sealed class ChatWithDataResponse
{
    [JsonPropertyName("choices")]
    public IList<ChatWithDataChoice> Choices { get; set; } = Array.Empty<ChatWithDataChoice>();
}

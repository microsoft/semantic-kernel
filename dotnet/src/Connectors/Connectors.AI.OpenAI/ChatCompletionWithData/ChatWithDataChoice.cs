// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

[Serializable]
internal sealed class ChatWithDataChoice
{
    [JsonPropertyName("messages")]
    public IList<ChatWithDataMessage> Messages { get; set; } = Array.Empty<ChatWithDataMessage>();
}

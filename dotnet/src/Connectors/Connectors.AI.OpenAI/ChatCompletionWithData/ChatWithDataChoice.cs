// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ChatCompletionWithData;

[Serializable]
[SuppressMessage("Performance", "CA1812:Avoid uninstantiated internal classes", Justification = "Used for JSON deserialization")]
internal sealed class ChatWithDataChoice
{
    [JsonPropertyName("messages")]
    public IList<ChatWithDataMessage> Messages { get; set; } = Array.Empty<ChatWithDataMessage>();
}

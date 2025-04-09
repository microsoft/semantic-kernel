// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// Response for chat completion.
/// </summary>
internal sealed class ChatCompletionResponse : MistralResponseBase
{
    [JsonPropertyName("created")]
    public int? Created { get; set; }

    [JsonPropertyName("choices")]
    public IList<MistralChatChoice>? Choices { get; set; }
}

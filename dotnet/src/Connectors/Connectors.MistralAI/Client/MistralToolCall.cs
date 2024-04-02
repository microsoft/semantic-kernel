// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;

/// <summary>
/// Tool call for chat completion.
/// </summary>
internal class MistralToolCall
{
    [JsonPropertyName("function")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public MistralFunction? Function { get; set; }
}

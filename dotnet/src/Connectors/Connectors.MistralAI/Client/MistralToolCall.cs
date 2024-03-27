// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.MistralAI.Client;
internal class MistralToolCall
{
    [JsonPropertyName("function")]
    public MistralFunction? Function { get; set; }
}

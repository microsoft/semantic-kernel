// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

internal sealed class EmbedRequest
{
    [JsonPropertyName("texts")]
    public IList<string> Texts { get; set; } = [];
    [JsonPropertyName("input_type")]
    public string InputType { get; set; } = "search_document";
}

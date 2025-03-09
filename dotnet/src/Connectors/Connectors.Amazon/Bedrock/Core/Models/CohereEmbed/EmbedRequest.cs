// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

internal sealed class EmbedRequest
{
    /// <summary>
    /// The provided input text strings for text embedding response.
    /// </summary>
    [JsonPropertyName("texts")]
    public IList<string> Texts { get; set; } = [];

    /// <summary>
    /// The input type for the text embedding response. Acceptable values are "search_document" or "search_query".
    /// </summary>
    [JsonPropertyName("input_type")]
    public string InputType { get; set; } = "search_document";
}

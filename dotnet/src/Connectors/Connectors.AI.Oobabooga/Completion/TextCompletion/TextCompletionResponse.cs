// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.Oobabooga.Completion.TextCompletion;

/// <summary>
/// HTTP Schema for Oobabooga completion response. Contains a list of results. Adapted from <see href="https://github.com/oobabooga/text-generation-webui/blob/main/extensions/api/blocking_api.py"/>
/// </summary>
public sealed class TextCompletionResponse
{
    /// <summary>
    /// A field used by Oobabooga to return results from the blocking API.
    /// </summary>
    [JsonPropertyName("results")]
    public List<TextCompletionResponseText> Results { get; set; } = new();
}

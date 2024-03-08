// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

internal sealed class OpenAIModerationRequest
{
    /// <summary>
    /// The input texts to classify.
    /// </summary>
    [JsonPropertyName("input")]
    public IList<string> Input { get; set; } = null!;

    /// <summary>
    /// Optional. Defaults to text-moderation-latest.
    /// </summary>
    [JsonPropertyName("model")]
    public string? Model { get; set; }

    public static OpenAIModerationRequest FromTexts(IList<string> texts, string modelId)
    {
        return new OpenAIModerationRequest
        {
            Input = texts,
            Model = modelId
        };
    }
}

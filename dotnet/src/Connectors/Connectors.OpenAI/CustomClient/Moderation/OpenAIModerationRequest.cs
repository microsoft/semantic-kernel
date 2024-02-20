// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

internal sealed class OpenAIModerationRequest
{
    /// <summary>
    /// The input text to classify.
    /// </summary>
    [JsonPropertyName("input")]
    public string Input { get; set; } = string.Empty;

    /// <summary>
    /// Optional. Defaults to text-moderation-latest.
    /// </summary>
    [JsonPropertyName("model")]
    public string? Model { get; set; }

    public static OpenAIModerationRequest FromText(string text, string modelId)
    {
        return new OpenAIModerationRequest
        {
            Input = text,
            Model = modelId
        };
    }
}

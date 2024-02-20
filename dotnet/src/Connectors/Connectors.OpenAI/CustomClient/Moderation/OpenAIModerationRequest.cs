// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

internal sealed class OpenAIModerationRequest
{
    /// <summary>
    /// The input text to classify.
    /// </summary>
    public string Input { get; set; } = string.Empty;

    /// <summary>
    /// Optional. Defaults to text-moderation-latest.
    /// </summary>
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

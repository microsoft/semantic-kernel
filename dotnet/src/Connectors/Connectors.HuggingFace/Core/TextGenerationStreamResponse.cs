// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

internal sealed class TextGenerationStreamResponse
{
    [JsonPropertyName("index")]
    public int Index { get; set; }

    [JsonPropertyName("token")]
    public TextGenerationToken? Token { get; set; }

    [JsonPropertyName("generated_text")]
    public string? GeneratedText { get; set; }

    [JsonPropertyName("details")]
    public string? Details { get; set; }

    internal sealed class TextGenerationToken
    {
        [JsonPropertyName("id")]
        public int Id { get; set; }

        [JsonPropertyName("text")]
        public string? Text { get; set; }

        [JsonPropertyName("logprob")]
        public double LogProb { get; set; }

        [JsonPropertyName("special")]
        public bool Special { get; set; }
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes

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
    public TextGenerationDetails? Details { get; set; }

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

    internal sealed class TextGenerationDetails
    {
        [JsonPropertyName("finish_reason")]
        public string? FinishReason { get; set; }

        [JsonPropertyName("generated_tokens")]
        public int GeneratedTokens { get; set; }

        [JsonPropertyName("seed")]
        public long? Seed { get; set; }
    }
}

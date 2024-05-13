// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

internal sealed class GeneratedTextItem
{
    [JsonPropertyName("generated_text")]
    public string? GeneratedText { get; set; }

    [JsonPropertyName("details")]
    public TextGenerationDetails? Details { get; set; }

    internal sealed class TextGenerationDetails
    {
        [JsonPropertyName("finish_reason")]
        public string? FinishReason { get; set; }

        [JsonPropertyName("generated_tokens")]
        public int GeneratedTokens { get; set; }

        [JsonPropertyName("seed")]
        public long? Seed { get; set; }

        [JsonPropertyName("prefill")]
        public List<TextGenerationPrefillToken>? Prefill { get; set; }

        [JsonPropertyName("tokens")]
        public List<TextGenerationToken>? Tokens { get; set; }
    }

    internal class TextGenerationPrefillToken
    {
        [JsonPropertyName("id")]
        public int Id { get; set; }

        [JsonPropertyName("text")]
        public string? Text { get; set; }

        [JsonPropertyName("logprob")]
        public double LogProb { get; set; }
    }

    internal sealed class TextGenerationToken : TextGenerationPrefillToken
    {
        [JsonPropertyName("special")]
        public bool Special { get; set; }
    }
}

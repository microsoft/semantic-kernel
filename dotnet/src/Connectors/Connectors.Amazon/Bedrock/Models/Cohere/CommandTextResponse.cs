// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Connectors.Amazon.Models.Cohere;

public class CommandTextResponse //FOR COHERE COMMAND NOT COMMAND R
{
    [JsonPropertyName("generations")]
    public List<Generation> Generations { get; set; }

    [JsonPropertyName("id")]
    public string Id { get; set; }

    [JsonPropertyName("prompt")]
    public string Prompt { get; set; }

    [Serializable]
    public class Generation
    {
        [JsonPropertyName("finish_reason")]
        public string FinishReason { get; set; }

        [JsonPropertyName("id")]
        public string Id { get; set; }

        [JsonPropertyName("text")]
        public string Text { get; set; }

        [JsonPropertyName("likelihood")]
        public double? Likelihood { get; set; }

        [JsonPropertyName("token_likelihoods")]
        public List<TokenLikelihood> TokenLikelihoods { get; set; }

        [JsonPropertyName("is_finished")]
        public bool IsFinished { get; set; }

        [JsonPropertyName("index")]
        public int? Index { get; set; }
    }

    [Serializable]
    public class TokenLikelihood
    {
        [JsonPropertyName("token")]
        public double Token { get; set; }
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Connectors.Amazon.Core.Requests;

namespace Connectors.Amazon.Models.Mistral;

public class MistralRequest
{
    [Serializable]
    public class MistralTextGenerationRequest : ITextGenerationRequest
    {
        [JsonPropertyName("prompt")]
        public required string Prompt { get; set; }

        [JsonPropertyName("max_tokens")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxTokens { get; set; }

        [JsonPropertyName("stop")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<string>? StopSequences { get; set; } = new List<string>();

        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? Temperature { get; set; }

        [JsonPropertyName("top_p")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? TopP { get; set; }

        [JsonPropertyName("top_k")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? TopK { get; set; }

        string ITextGenerationRequest.InputText => Prompt;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Connectors.Amazon.Core.Requests;

namespace Connectors.Amazon.Models.Meta;

public class LlamaTextRequest
{
    [Serializable]
    public class LlamaTextGenerationRequest : ITextGenerationRequest
    {
        [JsonPropertyName("prompt")]
        public required string Prompt { get; set; }

        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? Temperature { get; set; }

        [JsonPropertyName("top_p")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? TopP { get; set; }

        [JsonPropertyName("max_gen_len")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxGenLen { get; set; }

        string ITextGenerationRequest.InputText => Prompt;

        double? ITextGenerationRequest.TopP => TopP;

        double? ITextGenerationRequest.Temperature => Temperature;

        int? ITextGenerationRequest.MaxTokens => MaxGenLen;

        IList<string>? ITextGenerationRequest.StopSequences => null;
    }
}

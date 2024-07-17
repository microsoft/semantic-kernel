// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Connectors.Amazon.Core.Requests;

namespace Connectors.Amazon.Models.Meta;
/// <summary>
/// Text generation body for Meta Llama.
/// </summary>
public static class LlamaTextRequest
{
    /// <summary>
    /// Text generation request object for InvokeModel as required by Meta Llama.
    /// </summary>
    [Serializable]
    public sealed class LlamaTextGenerationRequest : ITextGenerationRequest
    {
        /// <summary>
        /// The prompt that you want to pass to the model.
        /// </summary>
        [JsonPropertyName("prompt")]
        public required string Prompt { get; set; }
        /// <summary>
        /// Use a lower value to decrease randomness in the response.
        /// </summary>
        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? Temperature { get; set; }
        /// <summary>
        /// Use a lower value to ignore less probable options. Set to 0 or 1.0 to disable.
        /// </summary>
        [JsonPropertyName("top_p")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? TopP { get; set; }
        /// <summary>
        /// Specify the maximum number of tokens to use in the generated response. The model truncates the response once the generated text exceeds max_gen_len.
        /// </summary>
        [JsonPropertyName("max_gen_len")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxGenLen { get; set; }

        string ITextGenerationRequest.InputText => this.Prompt;

        double? ITextGenerationRequest.TopP => this.TopP;

        double? ITextGenerationRequest.Temperature => this.Temperature;

        int? ITextGenerationRequest.MaxTokens => this.MaxGenLen;

        IList<string>? ITextGenerationRequest.StopSequences => null;
    }
}

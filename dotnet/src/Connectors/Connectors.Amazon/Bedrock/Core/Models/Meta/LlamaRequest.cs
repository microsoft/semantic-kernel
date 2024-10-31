// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

internal static class LlamaRequest
{
    /// <summary>
    /// Text generation request object for InvokeModel as required by Meta Llama.
    /// </summary>
    internal sealed class LlamaTextGenerationRequest
    {
        /// <summary>
        /// The prompt that you want to pass to the model.
        /// </summary>
        [JsonPropertyName("prompt")]
        public string? Prompt { get; set; }

        /// <summary>
        /// Use a lower value to decrease randomness in the response.
        /// </summary>
        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public float? Temperature { get; set; }

        /// <summary>
        /// Use a lower value to ignore less probable options. Set to 0 or 1.0 to disable.
        /// </summary>
        [JsonPropertyName("top_p")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public float? TopP { get; set; }

        /// <summary>
        /// Specify the maximum number of tokens to use in the generated response. The model truncates the response once the generated text exceeds max_gen_len.
        /// </summary>
        [JsonPropertyName("max_gen_len")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxGenLen { get; set; }
    }
}

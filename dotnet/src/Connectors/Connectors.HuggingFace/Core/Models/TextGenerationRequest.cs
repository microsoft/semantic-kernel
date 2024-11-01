﻿
// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

/// <summary>
/// HuggingFace text generation request object.
/// </summary>
internal sealed class TextGenerationRequest
{
    /// <summary>
    /// The input string to generate text for.
    /// </summary>
    [JsonPropertyName("inputs")]
    public string? Inputs { get; set; }

    /// <summary>
    /// Enable streaming
    /// </summary>
    [JsonPropertyName("stream")]
    public bool Stream { get; set; } = false;

    /// <summary>
    /// Parameters used by the model for generation.
    /// </summary>
    [JsonPropertyName("parameters")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public HuggingFaceTextParameters? Parameters { get; set; }

    /// <summary>
    /// Options used by the model for generation.
    /// </summary>
    [JsonPropertyName("options")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public HuggingFaceTextOptions? Options { get; set; }

    /// <summary>
    /// Converts a <see cref="PromptExecutionSettings" /> object to a <see cref="TextGenerationRequest" /> object.
    /// </summary>
    /// <param name="prompt">Prompt text for generation.</param>
    /// <param name="executionSettings">Execution settings to be used for the request.</param>
    /// <returns>TextGenerationRequest object.</returns>
    internal static TextGenerationRequest FromPromptAndExecutionSettings(string prompt, HuggingFacePromptExecutionSettings executionSettings)
    {
        return new TextGenerationRequest
        {
            Inputs = prompt,
            Parameters = new()
            {
                Temperature = executionSettings.Temperature,
                MaxNewTokens = executionSettings.MaxNewTokens,
                TopK = executionSettings.TopK,
                TopP = executionSettings.TopP,
                RepetitionPenalty = executionSettings.RepetitionPenalty,
                MaxTime = executionSettings.MaxTime,
                NumReturnSequences = executionSettings.ResultsPerPrompt,
                Details = executionSettings.Details,
                ReturnFullText = executionSettings.ReturnFullText,
                DoSample = executionSettings.DoSample,
            },
            Options = new()
            {
                UseCache = executionSettings.UseCache,
                WaitForModel = executionSettings.WaitForModel
            }
        };
    }

    internal sealed class HuggingFaceTextParameters
    {
        /// <summary>
        /// (Default: None). Number to define the top tokens considered within the sample operation to create new text.
        /// </summary>
        [JsonPropertyName("top_k")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? TopK { get; set; }

        /// <summary>
        /// (Default: None). Define the tokens that are within the sample operation of text generation.
        /// Add tokens in the sample for more probable to least probable until the sum of the probabilities
        /// is greater than top_p.
        /// </summary>
        [JsonPropertyName("top_p")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? TopP { get; set; }

        /// <summary>
        /// (Default: 1.0). Range (0.0-100.0). The temperature of the sampling operation.
        /// 1 means regular sampling, 0 means always take the highest score,
        /// 100.0 is getting closer to uniform probability.
        /// </summary>
        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? Temperature { get; set; } = 1;

        /// <summary>
        /// (Default: None). (0.0-100.0). The more a token is used within generation
        /// the more it is penalized to not be picked in successive generation passes.
        /// </summary>
        [JsonPropertyName("repetition_penalty")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? RepetitionPenalty { get; set; }

        /// <summary>
        /// (Default: None). Range (0-250). The amount of new tokens to be generated,
        /// this does not include the input length it is a estimate of the size of generated text you want.
        /// Each new tokens slows down the request, so look for balance between response times
        /// and length of text generated.
        /// </summary>
        [JsonPropertyName("max_new_tokens")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxNewTokens { get; set; }

        /// <summary>
        /// (Default: None). Range (0-120.0). The amount of time in seconds that the query should take maximum.
        /// Network can cause some overhead so it will be a soft limit.
        /// Use that in combination with max_new_tokens for best results.
        /// </summary>
        [JsonPropertyName("max_time")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? MaxTime { get; set; }

        /// <summary>
        /// (Default: True). If set to False, the return results will not contain the original query making it easier for prompting.
        /// </summary>
        [JsonPropertyName("return_full_text")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ReturnFullText { get; set; } = true;

        /// <summary>
        /// (Default: 1). The number of proposition you want to be returned.
        /// </summary>
        [JsonPropertyName("num_return_sequences")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? NumReturnSequences { get; set; } = 1;

        /// <summary>
        /// (Optional: True). Whether or not to use sampling, use greedy decoding otherwise.
        /// </summary>
        [JsonPropertyName("do_sample")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? DoSample { get; set; }

        /// <summary>
        /// (Optional: True) Whether or not to include the details of the generation.
        /// </summary>
        /// <remarks>
        /// Disabling this won't provide information about token usage.
        /// </remarks>
        [JsonPropertyName("details")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? Details { get; set; }
    }

    internal sealed class HuggingFaceTextOptions
    {
        /// <summary>
        /// (Default: true). There is a cache layer on the inference API to speedup requests we have already seen.
        /// Most models can use those results as is as models are deterministic (meaning the results will be the same anyway).
        /// However if you use a non deterministic model, you can set this parameter to prevent the caching mechanism from being
        /// used resulting in a real new query.
        /// </summary>
        [JsonPropertyName("use_cache")]
        public bool UseCache { get; set; } = true;

        /// <summary>
        /// (Default: false) If the model is not ready, wait for it instead of receiving 503.
        /// It limits the number of requests required to get your inference done.
        /// It is advised to only set this flag to true after receiving a 503 error as it will limit hanging in your application to known places.
        /// </summary>
        [JsonPropertyName("wait_for_model")]
        public bool WaitForModel { get; set; } = false;
    }
}

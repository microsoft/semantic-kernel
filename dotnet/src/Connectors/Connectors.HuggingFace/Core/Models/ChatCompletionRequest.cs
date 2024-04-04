
// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Client.Models;

/// <summary>
/// HuggingFace text generation request object.
/// </summary>
internal sealed class ChatCompletionRequest
{
    /// <summary>
    /// Model name to use for generation.
    /// </summary>
    [JsonPropertyName("model")]
    public string? Model { get; set; }

    /// <summary>
    /// Indicates whether to get the response as stream or not.
    /// </summary>
    [JsonPropertyName("stream")]
    public bool Stream { get; set; }

    [JsonPropertyName("messages")]
    public List<ChatMessage>? Messages { get; set; }

    /// <summary>
    /// Whether to return log probabilities of the output tokens or not. If true, returns the log probabilities of each
    /// output token returned in the content of message.
    /// </summary>
    [JsonPropertyName("logprobs")]
    public bool? LogProbs { get; set; }

    /// <summary>
    /// An integer between 0 and 5 specifying the number of most likely tokens to return at each token position, each with
    /// an associated log probability. logprobs must be set to true if this parameter is used.
    /// </summary>
    [JsonPropertyName("top_logprobs")]
    public int? TopLogProbs { get; set; }

    /// <summary>
    /// The maximum number of tokens that can be generated in the chat completion.
    /// </summary>
    [JsonPropertyName("max_tokens")]
    public int? MaxTokens { get; set; }

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far,
    /// increasing the model's likelihood to talk about new topics
    /// </summary>
    [JsonPropertyName("presence_penalty")]
    public float? PresencePenalty { get; set; }

    /// <summary>
    /// Up to 4 sequences where the API will stop generating further tokens.
    /// </summary>
    [JsonPropertyName("stop")]
    public List<string>? Stop { get; set; }

    /// <summary>
    /// The seed to use for generating a similar output.
    /// </summary>
    [JsonPropertyName("seed")]
    public long? Seed { get; set; }

    /// <summary>
    /// What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while
    /// lower values like 0.2 will make it more focused and deterministic.
    ///
    /// We generally recommend altering this or `top_p` but not both.
    /// </summary>
    [JsonPropertyName("temperature")]
    public float? Temperature { get; set; }

    /// <summary>
    /// An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the
    /// tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.
    /// </summary>
    [JsonPropertyName("top_p")]
    public float? TopP { get; set; }

    /// <summary>
    /// Converts a <see cref="PromptExecutionSettings" /> object to a <see cref="TextGenerationRequest" /> object.
    /// </summary>
    /// <param name="chatHistory">Chat history to be used for the request.</param>
    /// <param name="executionSettings">Execution settings to be used for the request.</param>
    /// <returns>TexGenerationtRequest object.</returns>
    internal static ChatCompletionRequest FromChatHistoryAndExecutionSettings(ChatHistory chatHistory, HuggingFacePromptExecutionSettings executionSettings)
    {
        return new ChatCompletionRequest
        {
            Messages = chatHistory.Select(message => new ChatMessage
            {
                Content = message.Content,
                Role = message.Role.ToString(),
            }).ToList(),
            PresencePenalty = executionSettings.PresencePenalty,
            LogProbs = executionSettings.LogProbs,
            Seed = executionSettings.Seed,
            Temperature = executionSettings.Temperature,
            Stop = executionSettings.Stop,
            MaxTokens = executionSettings.MaxTokens,
            Model = executionSettings.ModelId ?? "tgi", // Text Generation Inference
            TopP = executionSettings.TopP,
            TopLogProbs = executionSettings.TopLogProbs
        };
    }

    internal sealed class ChatMessageToolCall
    {
        [JsonPropertyName("id")]
        public string? Id { get; set; }

        [JsonPropertyName("type")]
        public string? Type { get; set; }

        [JsonPropertyName("function")]
        public ChatMessageFunction? Function { get; set; }
    }

    internal sealed class ChatMessageFunction
    {
        [JsonPropertyName("description")]
        public string? Description { get; set; }

        [JsonPropertyName("name")]
        public string? Name { get; set; }

        [JsonPropertyName("parameters")]
        public string? Parameters { get; set; }
    }

    internal sealed class ChatMessage
    {
        [JsonPropertyName("role")]
        public string? Role { get; set; }

        [JsonPropertyName("content")]
        public string? Content { get; set; }

        [JsonPropertyName("name")]
        public string? Name { get; set; }

        [JsonPropertyName("tool_calls")]
        public List<ChatMessageToolCall>? ToolCalls { get; set; }

        /// <summary>
        /// (Default: None). Float to define the tokens that are within the sample operation of text generation.
        /// Add tokens in the sample for more probable to least probable until the sum of the probabilities
        /// is greater than top_p.
        /// </summary>
        [JsonPropertyName("top_p")]
        public double? TopP { get; set; }

        /// <summary>
        /// (Default: 1.0). Float (0.0-100.0). The temperature of the sampling operation.
        /// 1 means regular sampling, 0 means always take the highest score,
        /// 100.0 is getting closer to uniform probability.
        /// </summary>
        [JsonPropertyName("temperature")]
        public double? Temperature { get; set; } = 1;

        /// <summary>
        /// (Default: None). Float (0.0-100.0). The more a token is used within generation
        /// the more it is penalized to not be picked in successive generation passes.
        /// </summary>
        [JsonPropertyName("repetition_penalty")]
        public double? RepetitionPenalty { get; set; }

        /// <summary>
        /// (Default: None). Int (0-250). The amount of new tokens to be generated,
        /// this does not include the input length it is a estimate of the size of generated text you want.
        /// Each new tokens slows down the request, so look for balance between response times
        /// and length of text generated.
        /// </summary>
        [JsonPropertyName("max_new_tokens")]
        public int? MaxNewTokens { get; set; }

        /// <summary>
        /// (Default: None). Float (0-120.0). The amount of time in seconds that the query should take maximum.
        /// Network can cause some overhead so it will be a soft limit.
        /// Use that in combination with max_new_tokens for best results.
        /// </summary>
        [JsonPropertyName("max_time")]
        public double? MaxTime { get; set; }

        /// <summary>
        /// (Default: True). Bool. If set to False, the return results will not contain the original query making it easier for prompting.
        /// </summary>
        [JsonPropertyName("return_full_text")]
        public bool ReturnFullText { get; set; } = true;

        /// <summary>
        /// (Default: 1). Integer. The number of proposition you want to be returned.
        /// </summary>
        [JsonPropertyName("num_return_sequences")]
        public int? NumReturnSequences { get; set; } = 1;

        /// <summary>
        /// (Optional: True). Bool. Whether or not to use sampling, use greedy decoding otherwise.
        /// </summary>
        [JsonPropertyName("do_sample")]
        public bool DoSample { get; set; } = true;
    }

    internal sealed class HuggingFaceTextOptions
    {
        /// <summary>
        /// (Default: true). Boolean. There is a cache layer on the inference API to speedup requests we have already seen.
        /// Most models can use those results as is as models are deterministic (meaning the results will be the same anyway).
        /// However if you use a non deterministic model, you can set this parameter to prevent the caching mechanism from being
        /// used resulting in a real new query.
        /// </summary>
        [JsonPropertyName("use_cache")]
        public bool UseCache { get; set; } = true;

        /// <summary>
        /// (Default: false) Boolean. If the model is not ready, wait for it instead of receiving 503.
        /// It limits the number of requests required to get your inference done.
        /// It is advised to only set this flag to true after receiving a 503 error as it will limit hanging in your application to known places.
        /// </summary>
        [JsonPropertyName("wait_for_model")]
        public bool WaitForModel { get; set; } = false;
    }
}

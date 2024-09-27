// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace.Core;

/// <summary>
/// HuggingFace text generation request object.
/// </summary>
internal sealed class ChatCompletionRequest
{
    /// <summary>
    /// This is the default name when using TGI and will be ignored as the TGI will only target the current activated model.
    /// </summary>
    private const string TextGenerationInferenceDefaultModel = "tgi";
    /// <summary>
    /// Model name to use for generation.
    /// </summary>
    /// <remarks>
    /// When using TGI this parameter will be ignored.
    /// </remarks>
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
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? LogProbs { get; set; }

    /// <summary>
    /// An integer between 0 and 5 specifying the number of most likely tokens to return at each token position, each with
    /// an associated log probability. logprobs must be set to true if this parameter is used.
    /// </summary>
    [JsonPropertyName("top_logprobs")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? TopLogProbs { get; set; }

    /// <summary>
    /// The maximum number of tokens that can be generated in the chat completion.
    /// </summary>
    [JsonPropertyName("max_tokens")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? MaxTokens { get; set; }

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far,
    /// increasing the model's likelihood to talk about new topics
    /// </summary>
    [JsonPropertyName("presence_penalty")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public float? PresencePenalty { get; set; }

    /// <summary>
    /// Up to 4 sequences where the API will stop generating further tokens.
    /// </summary>
    [JsonPropertyName("stop")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<string>? Stop { get; set; }

    /// <summary>
    /// The seed to use for generating a similar output.
    /// </summary>
    [JsonPropertyName("seed")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public long? Seed { get; set; }

    /// <summary>
    /// What sampling temperature to use, between 0 and 2. Higher values like 0.8 will make the output more random, while
    /// lower values like 0.2 will make it more focused and deterministic.
    ///
    /// We generally recommend altering this or `top_p` but not both.
    /// </summary>
    [JsonPropertyName("temperature")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public float? Temperature { get; set; }

    /// <summary>
    /// An alternative to sampling with temperature, called nucleus sampling, where the model considers the results of the
    /// tokens with top_p probability mass. So 0.1 means only the tokens comprising the top 10% probability mass are considered.
    /// </summary>
    [JsonPropertyName("top_p")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public float? TopP { get; set; }

    /// <summary>
    /// Converts a <see cref="PromptExecutionSettings" /> object to a <see cref="TextGenerationRequest" /> object.
    /// </summary>
    /// <param name="chatHistory">Chat history to be used for the request.</param>
    /// <param name="executionSettings">Execution settings to be used for the request.</param>
    /// <param name="modelId">Model id to use if value in prompt execution settings is not set.</param>
    /// <returns>TexGenerationRequest object.</returns>
    internal static ChatCompletionRequest FromChatHistoryAndExecutionSettings(ChatHistory chatHistory, HuggingFacePromptExecutionSettings executionSettings, string modelId)
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
            Model = executionSettings.ModelId ?? modelId ?? TextGenerationInferenceDefaultModel,
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
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? Name { get; set; }

        [JsonPropertyName("tool_calls")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public List<ChatMessageToolCall>? ToolCalls { get; set; }
    }
}

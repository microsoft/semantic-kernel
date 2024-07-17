// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;

namespace Connectors.Amazon.Models.AI21;
/// <summary>
/// AI21 Labs Request objects.
/// </summary>
public static class AI21JambaRequest
{
    /// <summary>
    /// Chat completion request object for AI21 Labs Jamba.
    /// </summary>
    public class AI21ChatCompletionRequest : IChatCompletionRequest
    {
        /// <summary>
        /// The previous messages in this chat, from oldest (index 0) to newest. Must have at least one user or assistant message in the list. Include both user inputs and system responses. Maximum total size for the list is about 256K tokens. Each message includes the following members:
        /// </summary>
        public List<Message>? Messages { get; set; }
        /// <summary>
        /// How much variation to provide in each answer. Setting this value to 0 guarantees the same response to the same question every time. Setting a higher value encourages more variation. Modifies the distribution from which tokens are sampled. Default: 1.0, Range: 0.0 – 2.0
        /// </summary>
        public double Temperature { get; set; } = 1.0;
        /// <summary>
        /// Limit the pool of next tokens in each step to the top N percentile of possible tokens, where 1.0 means the pool of all possible tokens, and 0.01 means the pool of only the most likely next tokens.
        /// </summary>
        public double TopP { get; set; } = 1.0;
        /// <summary>
        /// The maximum number of tokens to allow for each generated response message. Typically the best way to limit output length is by providing a length limit in the system prompt (for example, "limit your answers to three sentences"). Default: 4096, Range: 0 – 4096.
        /// </summary>
        public int MaxTokens { get; set; } = 4096;
        /// <summary>
        /// End the message when the model generates one of these strings. The stop sequence is not included in the generated message. Each sequence can be up to 64K long, and can contain newlines as \n characters.
        /// </summary>
        public List<string>? StopSequences { get; set; }
        /// <summary>
        /// How many chat responses to generate. Notes n must be 1 for streaming responses. If n is set to larger than 1, setting temperature=0 will always fail because all answers are guaranteed to be duplicates. Default:1, Range: 1 – 16
        /// </summary>
        public int NumResponses { get; set; } = 1;
        /// <summary>
        /// Reduce frequency of repeated words within a single response message by increasing this number. This penalty gradually increases the more times a word appears during response generation. Setting to 2.0 will produce a string with few, if any repeated words.
        /// </summary>
        public double FrequencyPenalty { get; set; }
        /// <summary>
        /// Reduce the frequency of repeated words within a single message by increasing this number. Unlike frequency penalty, presence penalty is the same no matter how many times a word appears.
        /// </summary>
        public double PresencePenalty { get; set; }
        /// <summary>
        /// A system prompt to pass to the model.
        /// </summary>
        public List<SystemContentBlock>? System { get; set; }
        /// <summary>
        /// Inference parameters to pass to the model. Converse supports a base set of inference parameters. If you need to pass additional parameters that the model supports, use the additionalModelRequestFields request field.
        /// </summary>
        public InferenceConfiguration? InferenceConfig { get; set; }
        /// <summary>
        /// Additional inference parameters that the model supports, beyond the base set of inference parameters that Converse supports in the inferenceConfig field.
        /// </summary>
        public Document AdditionalModelRequestFields { get; set; }
        /// <summary>
        /// Additional model parameters field paths to return in the response. Converse returns the requested fields as a JSON Pointer object in the additionalModelResponseFields field.
        /// </summary>
        public List<string>? AdditionalModelResponseFieldPaths { get; set; }
        /// <summary>
        /// Configuration information for a guardrail that you want to use in the request.
        /// </summary>
        public GuardrailConfiguration? GuardrailConfig { get; set; }
        /// <summary>
        /// The identifier for the model that you want to call.
        /// </summary>
        public string? ModelId { get; set; }
        /// <summary>
        /// Configuration information for the tools that the model can use when generating a response. This field is only supported by Anthropic Claude 3, Cohere Command R, Cohere Command R+, and Mistral Large models.
        /// </summary>
        public ToolConfiguration? ToolConfig { get; set; }
    }
    /// <summary>
    /// Text Generation Request object for AI21 Jamba.
    /// </summary>
    [Serializable]
    public sealed class AI21TextGenerationRequest : ITextGenerationRequest
    {
        /// <summary>
        /// InputText for the text generation request.
        /// </summary>
        [JsonIgnore]
        public string InputText
        {
            get
            {
                // Concatenating the content of all messages to form the input text
                return string.Join(" ", this.Messages.Select(m => m.Content));
            }
        }
        /// <summary>
        /// The previous messages in this chat, from oldest (index 0) to newest. Must have at least one user or assistant message in the list. Include both user inputs and system responses. Maximum total size for the list is about 256K tokens.
        /// </summary>
        [JsonPropertyName("messages")]
        public required List<Msg> Messages { get; set; }

        /// <summary>
        /// How many responses to generate (one for text generation).
        /// </summary>
        [JsonPropertyName("n")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? NumberOfResponses { get; set; }
        /// <summary>
        /// How much variation to provide in each answer. Setting this value to 0 guarantees the same response to the same question every time. Setting a higher value encourages more variation. Modifies the distribution from which tokens are sampled. Default: 1.0, Range: 0.0 – 2.0
        /// </summary>
        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? Temperature { get; set; }
        /// <summary>
        /// Limit the pool of next tokens in each step to the top N percentile of possible tokens, where 1.0 means the pool of all possible tokens, and 0.01 means the pool of only the most likely next tokens.
        /// </summary>
        [JsonPropertyName("top_p")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? TopP { get; set; }
        /// <summary>
        /// The maximum number of tokens to allow for each generated response message. Typically, the best way to limit output length is by providing a length limit in the system prompt (for example, "limit your answers to three sentences"). Default: 4096, Range: 0 – 4096.
        /// </summary>
        [JsonPropertyName("max_tokens")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxTokens { get; set; }
        /// <summary>
        /// End the message when the model generates one of these strings. The stop sequence is not included in the generated message. Each sequence can be up to 64K long, and can contain newlines as \n characters.
        /// </summary>
        [JsonPropertyName("stop")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<string>? Stop { get; set; }
        /// <summary>
        /// Reduce frequency of repeated words within a single response message by increasing this number. This penalty gradually increases the more times a word appears during response generation. Setting to 2.0 will produce a string with few, if any repeated words.
        /// </summary>
        [JsonPropertyName("frequency_penalty")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? FrequencyPenalty { get; set; }
        /// <summary>
        /// Reduce the frequency of repeated words within a single message by increasing this number. Unlike frequency penalty, presence penalty is the same no matter how many times a word appears.
        /// </summary>
        [JsonPropertyName("presence_penalty")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public double? PresencePenalty { get; set; }
        /// <summary>
        /// Max tokens as required parameter for text generation request.
        /// </summary>
        int? ITextGenerationRequest.MaxTokens => this.MaxTokens;
        /// <summary>
        /// TopP as required parameter for text generation request.
        /// </summary>
        double? ITextGenerationRequest.TopP => this.TopP;
        /// <summary>
        /// Temperature as required parameter for text generation request.
        /// </summary>
        double? ITextGenerationRequest.Temperature => this.Temperature;
        /// <summary>
        /// Stop sequences as required parameter for text generation request.
        /// </summary>
        IList<string>? ITextGenerationRequest.StopSequences => this.Stop;
    }
    /// <summary>
    /// Message object for AI21 Labs Jamba which has the role and content.
    /// </summary>
    [Serializable]
    public class Msg
    {
        /// <summary>
        /// Role of the message written (assistant, user, or system).
        /// </summary>
        [JsonPropertyName("role")]
        public required string Role { get; set; }
        /// <summary>
        /// Message contents.
        /// </summary>
        [JsonPropertyName("content")]
        public required string Content { get; set; }
    }
}

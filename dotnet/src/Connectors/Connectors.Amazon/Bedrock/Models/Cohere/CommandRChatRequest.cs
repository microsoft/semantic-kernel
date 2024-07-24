// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;
using Amazon.BedrockRuntime.Model;
using Amazon.Runtime.Documents;
using Connectors.Amazon.Core.Requests;

namespace Connectors.Amazon.Models.Cohere;

/// <summary>
/// Cohere Command Chat Completion Request body.
/// </summary>
public class CohereCommandRequest : IChatCompletionRequest
{
    /// <summary>
    /// (Required) Text input for the model to respond to.
    /// </summary>
    [JsonPropertyName("message")]
    public string? Message { get; set; }
    /// <inheritdoc />
    public List<Message>? Messages { get; set; }
    /// <summary>
    /// A list of previous messages between the user and the model, meant to give the model conversational context for responding to the user's message.
    /// </summary>
    [JsonPropertyName("chat_history")]
    public List<CohereMessage>? ChatHistory { get; set; }
    /// <summary>
    /// A list of texts that the model can cite to generate a more accurate reply. Each document is a string-string dictionary. The resulting generation includes citations that reference some of these documents. We recommend that you keep the total word count of the strings in the dictionary to under 300 words. An _excludes field (array of strings) can be optionally supplied to omit some key-value pairs from being shown to the model.
    /// </summary>
    [JsonPropertyName("documents")]
    public List<CohereDocument>? Documents { get; set; }
    /// <summary>
    /// Defaults to false. When true, the response will only contain a list of generated search queries, but no search will take place, and no reply from the model to the user's message will be generated.
    /// </summary>
    [JsonPropertyName("search_queries_only")]
    public bool SearchQueriesOnly { get; set; } = false;
    /// <summary>
    /// Overrides the default preamble for search query generation. Has no effect on tool use generations.
    /// </summary>
    [JsonPropertyName("preamble")]
    public string? Preamble { get; set; }
    /// <summary>
    /// The maximum number of tokens the model should generate as part of the response. Note that setting a low value may result in incomplete generations. Setting max_tokens may result in incomplete or no generations when used with the tools or documents fields.
    /// </summary>
    [JsonPropertyName("max_tokens")]
    public int MaxTokens { get; set; }
    /// <summary>
    /// Use a lower value to decrease randomness in the response. Randomness can be further maximized by increasing the value of the p parameter.
    /// </summary>
    [JsonPropertyName("temperature")]
    public float Temperature { get; set; }
    /// <summary>
    /// Top P. Use a lower value to ignore less probable options.
    /// </summary>
    [JsonPropertyName("p")]
    public float TopP { get; set; }
    /// <summary>
    /// Top K. Specify the number of token choices the model uses to generate the next token.
    /// </summary>
    [JsonPropertyName("k")]
    public float TopK { get; set; }
    /// <summary>
    /// Defaults to OFF. Dictates how the prompt is constructed. With prompt_truncation set to AUTO_PRESERVE_ORDER, some elements from chat_history and documents will be dropped to construct a prompt that fits within the model's context length limit. During this process the order of the documents and chat history will be preserved. With prompt_truncation` set to OFF, no elements will be dropped.
    /// </summary>
    [JsonPropertyName("prompt_truncation")]
    public string PromptTruncation { get; set; }
    /// <summary>
    /// Used to reduce repetitiveness of generated tokens. The higher the value, the stronger a penalty is applied to previously present tokens, proportional to how many times they have already appeared in the prompt or prior generation.
    /// </summary>
    [JsonPropertyName("frequency_penalty")]
    public double FrequencyPenalty { get; set; }
    /// <summary>
    /// Used to reduce repetitiveness of generated tokens. Similar to frequency_penalty, except that this penalty is applied equally to all tokens that have already appeared, regardless of their exact frequencies.
    /// </summary>
    [JsonPropertyName("presence_penalty")]
    public double PresencePenalty { get; set; }
    /// <summary>
    /// If specified, the backend will make a best effort to sample tokens deterministically, such that repeated requests with the same seed and parameters should return the same result. However, determinism cannot be totally guaranteed.
    /// </summary>
    [JsonPropertyName("seed")]
    public int Seed { get; set; }
    /// <summary>
    /// Specify true to return the full prompt that was sent to the model. The default value is false. In the response, the prompt in the prompt field.
    /// </summary>
    [JsonPropertyName("return_prompt")]
    public bool ReturnPrompt { get; set; }
    /// <summary>
    /// A list of available tools (functions) that the model may suggest invoking before producing a text response. When tools is passed (without tool_results), the text field in the response will be "" and the tool_calls field in the response will be populated with a list of tool calls that need to be made. If no calls need to be made, the tool_calls array will be empty.
    /// </summary>
    [JsonPropertyName("tools")]
    public List<CohereTool>? Tools { get; set; }
    /// <summary>
    /// A list of results from invoking tools recommended by the model in the previous chat turn. Results are used to produce a text response and are referenced in citations. When using tool_results, tools must be passed as well. Each tool_result contains information about how it was invoked, as well as a list of outputs in the form of dictionaries. Cohere’s unique fine-grained citation logic requires the output to be a list. In case the output is just one item, such as {"status": 200}, you should still wrap it inside a list.
    /// </summary>
    [JsonPropertyName("tool_results")]
    public List<CohereToolResult>? ToolResults { get; set; }
    /// <summary>
    /// A list of stop sequences. After a stop sequence is detected, the model stops generating further tokens.
    /// </summary>
    [JsonPropertyName("stop_sequences")]
    public List<string>? StopSequences { get; set; }
    /// <summary>
    /// Specify true, to send the user’s message to the model without any preprocessing, otherwise false.
    /// </summary>
    [JsonPropertyName("raw_prompting")]
    public bool RawPrompting { get; set; }
    /// <inheritdoc />
    public List<SystemContentBlock>? System { get; set; }
    /// <inheritdoc />
    public InferenceConfiguration? InferenceConfig { get; set; }
    /// <inheritdoc />
    public Document AdditionalModelRequestFields { get; set; }
    /// <inheritdoc />
    public List<string>? AdditionalModelResponseFieldPaths { get; set; }
    /// <inheritdoc />
    public GuardrailConfiguration? GuardrailConfig { get; set; }
    /// <inheritdoc />
    public string? ModelId { get; set; }
    /// <inheritdoc />
    public ToolConfiguration? ToolConfig { get; set; }
    /// <summary>
    /// The required fields for chat_history.
    /// </summary>
    public class CohereMessage
    {
        /// <summary>
        /// The role for the message. Valid values are USER or CHATBOT. tokens.
        /// </summary>
        [JsonPropertyName("role")]
        public string? Role { get; set; }
        /// <summary>
        /// Text contents of the message.
        /// </summary>
        [JsonPropertyName("message")]
        public string? Message { get; set; }
    }
    /// <summary>
    /// JSON structure for list of texts that the model can cite to generate a more accurate reply.
    /// </summary>
    public class CohereDocument
    {
        /// <summary>
        /// Possible key field.
        /// </summary>
        [JsonPropertyName("title")]
        public string? Title { get; set; }
        /// <summary>
        /// Possible value field.
        /// </summary>
        [JsonPropertyName("snippet")]
        public string? Snippet { get; set; }
    }
    /// <summary>
    /// Tool parameters.
    /// </summary>
    public class CohereTool
    {
        /// <summary>
        /// Name of the tool.
        /// </summary>
        [JsonPropertyName("name")]
        public string? Name { get; set; }
        /// <summary>
        /// Description of the tool.
        /// </summary>
        [JsonPropertyName("description")]
        public string? Description { get; set; }
        /// <summary>
        /// Definitions for each tool.
        /// </summary>
        [JsonPropertyName("parameter_definitions")]
        public Dictionary<string, CohereToolParameter>? ParameterDefinitions { get; set; }
    }
    /// <summary>
    /// Components of each tool parameter.
    /// </summary>
    public class CohereToolParameter
    {
        /// <summary>
        /// Description of parameter.
        /// </summary>
        [JsonPropertyName("description")]
        public string? Description { get; set; }
        /// <summary>
        /// Parameter type (str, int, etc.) as described in a string.
        /// </summary>
        [JsonPropertyName("type")]
        public string? Type { get; set; }
        /// <summary>
        /// Whether this parameter is required.
        /// </summary>
        [JsonPropertyName("required")]
        public bool Required { get; set; }
    }
    /// <summary>
    /// Cohere tool result.
    /// </summary>
    public class CohereToolResult
    {
        /// <summary>
        /// The tool call.
        /// </summary>
        [JsonPropertyName("call")]
        public CohereToolCall? Call { get; set; }
        /// <summary>
        /// Outputs from the tool call.
        /// </summary>
        [JsonPropertyName("outputs")]
        public List<Document>? Outputs { get; set; }
    }
    /// <summary>
    /// Tool call object to be passed into the tool call.
    /// </summary>
    public class CohereToolCall
    {
        /// <summary>
        /// Name of tool.
        /// </summary>
        [JsonPropertyName("name")]
        public string? Name { get; set; }
        /// <summary>
        /// Parameters for the tool.
        /// </summary>
        [JsonPropertyName("parameters")]
        public Dictionary<string, string>? Parameters { get; set; }
    }
}

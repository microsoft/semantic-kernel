// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Amazon.Core;

/// <summary>
/// Request object for the Command-R model.
/// </summary>
internal static class CommandRRequest
{
    /// <summary>
    /// Text generation request object.
    /// </summary>
    internal sealed class CommandRTextGenerationRequest
    {
        /// <summary>
        /// (Required) Text input for the model to respond to.
        /// </summary>
        [JsonPropertyName("message")]
        public string? Message { get; set; }

        /// <summary>
        /// A list of previous messages between the user and the model, meant to give the model conversational context for responding to the user's message.
        /// </summary>
        [JsonPropertyName("chat_history")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<CohereCommandRTools.ChatMessage>? ChatHistory { get; set; }

        /// <summary>
        /// A list of texts that the model can cite to generate a more accurate reply. Each document is a string-string dictionary. The resulting generation includes citations that reference some of these documents. We recommend that you keep the total word count of the strings in the dictionary to under 300 words. An _excludes field (array of strings) can be optionally supplied to omit some key-value pairs from being shown to the model.
        /// </summary>
        [JsonPropertyName("documents")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<CohereCommandRTools.Document>? Documents { get; set; }

        /// <summary>
        /// Defaults to false. When true, the response will only contain a list of generated search queries, but no search will take place, and no reply from the model to the user's message will be generated.
        /// </summary>
        [JsonPropertyName("search_queries_only")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? SearchQueriesOnly { get; set; }

        /// <summary>
        /// Overrides the default preamble for search query generation. Has no effect on tool use generations.
        /// </summary>
        [JsonPropertyName("preamble")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? Preamble { get; set; }

        /// <summary>
        /// The maximum number of tokens the model should generate as part of the response. Note that setting a low value may result in incomplete generations. Setting max_tokens may result in incomplete or no generations when used with the tools or documents fields.
        /// </summary>
        [JsonPropertyName("max_tokens")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? MaxTokens { get; set; }

        /// <summary>
        /// Use a lower value to decrease randomness in the response. Randomness can be further maximized by increasing the value of the p parameter.
        /// </summary>
        [JsonPropertyName("temperature")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public float? Temperature { get; set; }

        /// <summary>
        /// Top P. Use a lower value to ignore less probable options.
        /// </summary>
        [JsonPropertyName("p")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public float? TopP { get; set; }

        /// <summary>
        /// Top K. Specify the number of token choices the model uses to generate the next token.
        /// </summary>
        [JsonPropertyName("k")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public float? TopK { get; set; }

        /// <summary>
        /// Defaults to OFF. Dictates how the prompt is constructed. With prompt_truncation set to AUTO_PRESERVE_ORDER, some elements from chat_history and documents will be dropped to construct a prompt that fits within the model's context length limit. During this process the order of the documents and chat history will be preserved. With prompt_truncation` set to OFF, no elements will be dropped.
        /// </summary>
        [JsonPropertyName("prompt_truncation")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public string? PromptTruncation { get; set; }

        /// <summary>
        /// Used to reduce repetitiveness of generated tokens. The higher the value, the stronger a penalty is applied to previously present tokens, proportional to how many times they have already appeared in the prompt or prior generation.
        /// </summary>
        [JsonPropertyName("frequency_penalty")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public float? FrequencyPenalty { get; set; }

        /// <summary>
        /// Used to reduce repetitiveness of generated tokens. Similar to frequency_penalty, except that this penalty is applied equally to all tokens that have already appeared, regardless of their exact frequencies.
        /// </summary>
        [JsonPropertyName("presence_penalty")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public float? PresencePenalty { get; set; }

        /// <summary>
        /// If specified, the backend will make a best effort to sample tokens deterministically, such that repeated requests with the same seed and parameters should return the same result. However, determinism cannot be totally guaranteed.
        /// </summary>
        [JsonPropertyName("seed")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public int? Seed { get; set; }

        /// <summary>
        /// Specify true to return the full prompt that was sent to the model. The default value is false. In the response, the prompt in the prompt field.
        /// </summary>
        [JsonPropertyName("return_prompt")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? ReturnPrompt { get; set; }

        /// <summary>
        /// A list of available tools (functions) that the model may suggest invoking before producing a text response. When tools is passed (without tool_results), the text field in the response will be "" and the tool_calls field in the response will be populated with a list of tool calls that need to be made. If no calls need to be made, the tool_calls array will be empty.
        /// </summary>
        [JsonPropertyName("tools")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
        public IList<CohereCommandRTools.Tool>? Tools { get; set; }

        /// <summary>
        /// A list of results from invoking tools recommended by the model in the previous chat turn. Results are used to produce a text response and are referenced in citations. When using tool_results, tools must be passed as well. Each tool_result contains information about how it was invoked, as well as a list of outputs in the form of dictionaries. Cohere’s unique fine-grained citation logic requires the output to be a list. In case the output is just one item, such as {"status": 200}, you should still wrap it inside a list.
        /// </summary>
        [JsonPropertyName("tool_results")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
        public IList<CohereCommandRTools.ToolResult>? ToolResults { get; set; }

        /// <summary>
        /// A list of stop sequences. After a stop sequence is detected, the model stops generating further tokens.
        /// </summary>
        [JsonPropertyName("stop_sequences")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public IList<string>? StopSequences { get; set; }

        /// <summary>
        /// Specify true, to send the user’s message to the model without any preprocessing, otherwise false.
        /// </summary>
        [JsonPropertyName("raw_prompting")]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public bool? RawPrompting { get; set; }
    }
}

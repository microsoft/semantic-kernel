// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Amazon;

/// <summary>
/// Prompt execution settings for Cohere Command-R
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public class AmazonCommandRExecutionSettings : PromptExecutionSettings
{
    private List<CohereCommandRTools.ChatMessage>? _chatHistory;
    private List<CohereCommandRTools.Document>? _documents;
    private bool? _searchQueriesOnly;
    private string? _preamble;
    private int? _maxTokens;
    private float? _temperature;
    private float? _topP;
    private float? _topK;
    private string? _promptTruncation;
    private float? _frequencyPenalty;
    private float? _presencePenalty;
    private int? _seed;
    private bool? _returnPrompt;
    private List<CohereCommandRTools.Tool>? _tools;
    private List<CohereCommandRTools.ToolResult>? _toolResults;
    private List<string>? _stopSequences;
    private bool? _rawPrompting;

    /// <summary>
    /// A list of previous messages between the user and the model, meant to give the model conversational context for responding to the user's message.
    /// </summary>
    [JsonPropertyName("chat_history")]
    public List<CohereCommandRTools.ChatMessage>? ChatHistory
    {
        get => this._chatHistory;
        set
        {
            this.ThrowIfFrozen();
            this._chatHistory = value;
        }
    }

    /// <summary>
    /// A list of texts that the model can cite to generate a more accurate reply. Each document is a string-string dictionary. The resulting generation includes citations that reference some of these documents. We recommend that you keep the total word count of the strings in the dictionary to under 300 words. An _excludes field (array of strings) can be optionally supplied to omit some key-value pairs from being shown to the model.
    /// </summary>
    [JsonPropertyName("documents")]
    public List<CohereCommandRTools.Document>? Documents
    {
        get => this._documents;
        set
        {
            this.ThrowIfFrozen();
            this._documents = value;
        }
    }

    /// <summary>
    /// Defaults to false. When true, the response will only contain a list of generated search queries, but no search will take place, and no reply from the model to the user's message will be generated.
    /// </summary>
    [JsonPropertyName("search_queries_only")]
    [JsonConverter(typeof(OptionalBoolJsonConverter))]
    public bool? SearchQueriesOnly
    {
        get => this._searchQueriesOnly;
        set
        {
            this.ThrowIfFrozen();
            this._searchQueriesOnly = value;
        }
    }

    /// <summary>
    /// Overrides the default preamble for search query generation. Has no effect on tool use generations.
    /// </summary>
    [JsonPropertyName("preamble")]
    public string? Preamble
    {
        get => this._preamble;
        set
        {
            this.ThrowIfFrozen();
            this._preamble = value;
        }
    }

    /// <summary>
    /// The maximum number of tokens the model should generate as part of the response. Note that setting a low value may result in incomplete generations. Setting max_tokens may result in incomplete or no generations when used with the tools or documents fields.
    /// </summary>
    [JsonPropertyName("max_tokens")]
    public int? MaxTokens
    {
        get => this._maxTokens;
        set
        {
            this.ThrowIfFrozen();
            this._maxTokens = value;
        }
    }

    /// <summary>
    /// Use a lower value to decrease randomness in the response. Randomness can be further maximized by increasing the value of the p parameter.
    /// </summary>
    [JsonPropertyName("temperature")]
    public float? Temperature
    {
        get => this._temperature;
        set
        {
            this.ThrowIfFrozen();
            this._temperature = value;
        }
    }

    /// <summary>
    /// Top P. Use a lower value to ignore less probable options.
    /// </summary>
    [JsonPropertyName("p")]
    public float? TopP
    {
        get => this._topP;
        set
        {
            this.ThrowIfFrozen();
            this._topP = value;
        }
    }

    /// <summary>
    /// Top K. Specify the number of token choices the model uses to generate the next token.
    /// </summary>
    [JsonPropertyName("k")]
    public float? TopK
    {
        get => this._topK;
        set
        {
            this.ThrowIfFrozen();
            this._topK = value;
        }
    }

    /// <summary>
    /// Defaults to OFF. Dictates how the prompt is constructed. With prompt_truncation set to AUTO_PRESERVE_ORDER, some elements from chat_history and documents will be dropped to construct a prompt that fits within the model's context length limit. During this process the order of the documents and chat history will be preserved. With prompt_truncation` set to OFF, no elements will be dropped.
    /// </summary>
    [JsonPropertyName("prompt_truncation")]
    public string? PromptTruncation
    {
        get => this._promptTruncation;
        set
        {
            this.ThrowIfFrozen();
            this._promptTruncation = value;
        }
    }

    /// <summary>
    /// Used to reduce repetitiveness of generated tokens. The higher the value, the stronger a penalty is applied to previously present tokens, proportional to how many times they have already appeared in the prompt or prior generation.
    /// </summary>
    [JsonPropertyName("frequency_penalty")]
    public float? FrequencyPenalty
    {
        get => this._frequencyPenalty;
        set
        {
            this.ThrowIfFrozen();
            this._frequencyPenalty = value;
        }
    }

    /// <summary>
    /// Used to reduce repetitiveness of generated tokens. Similar to frequency_penalty, except that this penalty is applied equally to all tokens that have already appeared, regardless of their exact frequencies.
    /// </summary>
    [JsonPropertyName("presence_penalty")]
    public float? PresencePenalty
    {
        get => this._presencePenalty;
        set
        {
            this.ThrowIfFrozen();
            this._presencePenalty = value;
        }
    }

    /// <summary>
    /// If specified, the backend will make a best effort to sample tokens deterministically, such that repeated requests with the same seed and parameters should return the same result. However, determinism cannot be totally guaranteed.
    /// </summary>
    [JsonPropertyName("seed")]
    public int? Seed
    {
        get => this._seed;
        set
        {
            this.ThrowIfFrozen();
            this._seed = value;
        }
    }

    /// <summary>
    /// Specify true to return the full prompt that was sent to the model. The default value is false. In the response, the prompt in the prompt field.
    /// </summary>
    [JsonPropertyName("return_prompt")]
    [JsonConverter(typeof(OptionalBoolJsonConverter))]
    public bool? ReturnPrompt
    {
        get => this._returnPrompt;
        set
        {
            this.ThrowIfFrozen();
            this._returnPrompt = value;
        }
    }

    /// <summary>
    /// A list of available tools (functions) that the model may suggest invoking before producing a text response. When tools is passed (without tool_results), the text field in the response will be "" and the tool_calls field in the response will be populated with a list of tool calls that need to be made. If no calls need to be made, the tool_calls array will be empty.
    /// </summary>
    [JsonPropertyName("tools")]
    public List<CohereCommandRTools.Tool>? Tools
    {
        get => this._tools;
        set
        {
            this.ThrowIfFrozen();
            this._tools = value;
        }
    }

    /// <summary>
    /// A list of results from invoking tools recommended by the model in the previous chat turn. Results are used to produce a text response and are referenced in citations. When using tool_results, tools must be passed as well. Each tool_result contains information about how it was invoked, as well as a list of outputs in the form of dictionaries. Cohere's unique fine-grained citation logic requires the output to be a list. In case the output is just one item, such as {"status": 200}, you should still wrap it inside a list.
    /// </summary>
    [JsonPropertyName("tool_results")]
    public List<CohereCommandRTools.ToolResult>? ToolResults
    {
        get => this._toolResults;
        set
        {
            this.ThrowIfFrozen();
            this._toolResults = value;
        }
    }

    /// <summary>
    /// A list of stop sequences. After a stop sequence is detected, the model stops generating further tokens.
    /// </summary>
    [JsonPropertyName("stop_sequences")]
    public List<string>? StopSequences
    {
        get => this._stopSequences;
        set
        {
            this.ThrowIfFrozen();
            this._stopSequences = value;
        }
    }

    /// <summary>
    /// Specify true, to send the user's message to the model without any preprocessing, otherwise false.
    /// </summary>
    [JsonPropertyName("raw_prompting")]
    [JsonConverter(typeof(OptionalBoolJsonConverter))]
    public bool? RawPrompting
    {
        get => this._rawPrompting;
        set
        {
            this.ThrowIfFrozen();
            this._rawPrompting = value;
        }
    }

    /// <summary>
    /// Converts PromptExecutionSettings to AmazonCommandExecutionSettings
    /// </summary>
    /// <param name="executionSettings">The Kernel standard PromptExecutionSettings.</param>
    /// <returns>Model specific execution settings</returns>
    public static AmazonCommandRExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        switch (executionSettings)
        {
            case null:
                return new AmazonCommandRExecutionSettings();
            case AmazonCommandRExecutionSettings settings:
                return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);
        return JsonSerializer.Deserialize<AmazonCommandRExecutionSettings>(json, JsonOptionsCache.ReadPermissive)!;
    }
}

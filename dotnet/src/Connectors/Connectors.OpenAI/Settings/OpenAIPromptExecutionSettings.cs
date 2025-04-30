// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Text;
using OpenAI.Chat;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Execution settings for an OpenAI completion request.
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public class OpenAIPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Gets or sets an object specifying the effort level for the model to use when generating the completion.
    /// </summary>
    /// <remarks>
    /// Constrains effort on reasoning for reasoning models.
    /// Reducing reasoning effort can result in faster responses and fewer tokens used on reasoning in a response.
    /// Possible values are:
    /// <para>- <see cref="string"/> values: <c>"low"</c>, <c>"medium"</c>, <c>"high"</c>;</para>
    /// <para>- <see cref="ChatReasoningEffortLevel"/> object;</para>
    /// </remarks>
    [JsonPropertyName("reasoning_effort")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? ReasoningEffort
    {
        get => this._reasoningEffort;
        set
        {
            this.ThrowIfFrozen();
            this._reasoningEffort = value;
        }
    }

    /// <summary>
    /// Temperature controls the randomness of the completion.
    /// The higher the temperature, the more random the completion.
    /// Default is 1.0.
    /// </summary>
    [JsonPropertyName("temperature")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? Temperature
    {
        get => this._temperature;

        set
        {
            this.ThrowIfFrozen();
            this._temperature = value;
        }
    }

    /// <summary>
    /// TopP controls the diversity of the completion.
    /// The higher the TopP, the more diverse the completion.
    /// Default is 1.0.
    /// </summary>
    [JsonPropertyName("top_p")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? TopP
    {
        get => this._topP;

        set
        {
            this.ThrowIfFrozen();
            this._topP = value;
        }
    }

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on whether they appear in the text so far, increasing the
    /// model's likelihood to talk about new topics.
    /// </summary>
    [JsonPropertyName("presence_penalty")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? PresencePenalty
    {
        get => this._presencePenalty;

        set
        {
            this.ThrowIfFrozen();
            this._presencePenalty = value;
        }
    }

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on their existing frequency in the text so far, decreasing
    /// the model's likelihood to repeat the same line verbatim.
    /// </summary>
    [JsonPropertyName("frequency_penalty")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? FrequencyPenalty
    {
        get => this._frequencyPenalty;

        set
        {
            this.ThrowIfFrozen();
            this._frequencyPenalty = value;
        }
    }

    /// <summary>
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    [JsonPropertyName("max_tokens")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
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
    /// Sequences where the completion will stop generating further tokens.
    /// </summary>
    [JsonPropertyName("stop_sequences")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IList<string>? StopSequences
    {
        get => this._stopSequences;

        set
        {
            this.ThrowIfFrozen();
            this._stopSequences = value;
        }
    }

    /// <summary>
    /// If specified, the system will make a best effort to sample deterministically such that repeated requests with the
    /// same seed and parameters should return the same result. Determinism is not guaranteed.
    /// </summary>
    [JsonPropertyName("seed")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public long? Seed
    {
        get => this._seed;

        set
        {
            this.ThrowIfFrozen();
            this._seed = value;
        }
    }

    /// <summary>
    /// Gets or sets the response format to use for the completion.
    /// </summary>
    /// <remarks>
    /// An object specifying the format that the model must output.
    /// Setting to <c>{ "type": "json_schema", "json_schema": { ...} }</c> enables Structured Outputs which ensures the model will match your supplied JSON schema. Learn more in the Structured Outputs guide.
    /// Setting to <c>{ "type": "json_object" }</c> enables JSON mode, which ensures the message the model generates is valid JSON.
    /// Important: when using JSON mode, you must also instruct the model to produce JSON yourself via a system or user message. Without this, the model may generate an unending stream of whitespace until the generation reaches the token limit, resulting in a long-running and seemingly "stuck" request. Also note that the message content may be partially cut off if finish_reason= "length", which indicates the generation exceeded max_tokens or the conversation exceeded the max context length.
    /// Possible values are:
    /// <para>- <see cref="string"/> values: <c>"json_object"</c>, <c>"text"</c>;</para>
    /// <para>- <see cref="ChatResponseFormat"/> object;</para>
    /// <para>- <see cref="Type"/> object, which will be used to automatically create a JSON schema.</para>
    /// </remarks>
    [JsonPropertyName("response_format")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? ResponseFormat
    {
        get => this._responseFormat;

        set
        {
            this.ThrowIfFrozen();
            this._responseFormat = value;
        }
    }

    /// <summary>
    /// The system prompt to use when generating text using a chat model.
    /// Defaults to "Assistant is a large language model."
    /// </summary>
    [JsonPropertyName("chat_system_prompt")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? ChatSystemPrompt
    {
        get => this._chatSystemPrompt;

        set
        {
            this.ThrowIfFrozen();
            this._chatSystemPrompt = value;
        }
    }

    /// <summary>
    /// The system prompt to use when generating text using a chat model.
    /// Defaults to "Assistant is a large language model."
    /// </summary>
    [Experimental("SKEXP0010")]
    [JsonPropertyName("chat_developer_prompt")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? ChatDeveloperPrompt
    {
        get => this._chatDeveloperPrompt;

        set
        {
            this.ThrowIfFrozen();
            this._chatDeveloperPrompt = value;
        }
    }

    /// <summary>
    /// Modify the likelihood of specified tokens appearing in the completion.
    /// </summary>
    [JsonPropertyName("token_selection_biases")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IDictionary<int, int>? TokenSelectionBiases
    {
        get => this._tokenSelectionBiases;

        set
        {
            this.ThrowIfFrozen();
            this._tokenSelectionBiases = value;
        }
    }

    /// <summary>
    /// Gets or sets the behavior for how tool calls are handled.
    /// </summary>
    /// <remarks>
    /// <list type="bullet">
    /// <item>To disable all tool calling, set the property to null (the default).</item>
    /// <item>
    /// To request that the model use a specific function, set the property to an instance returned
    /// from <see cref="ToolCallBehavior.RequireFunction"/>.
    /// </item>
    /// <item>
    /// To allow the model to request one of any number of functions, set the property to an
    /// instance returned from <see cref="ToolCallBehavior.EnableFunctions"/>, called with
    /// a list of the functions available.
    /// </item>
    /// <item>
    /// To allow the model to request one of any of the functions in the supplied <see cref="Kernel"/>,
    /// set the property to <see cref="ToolCallBehavior.EnableKernelFunctions"/> if the client should simply
    /// send the information about the functions and not handle the response in any special manner, or
    /// <see cref="ToolCallBehavior.AutoInvokeKernelFunctions"/> if the client should attempt to automatically
    /// invoke the function and send the result back to the service.
    /// </item>
    /// </list>
    /// For all options where an instance is provided, auto-invoke behavior may be selected. If the service
    /// sends a request for a function call, if auto-invoke has been requested, the client will attempt to
    /// resolve that function from the functions available in the <see cref="Kernel"/>, and if found, rather
    /// than returning the response back to the caller, it will handle the request automatically, invoking
    /// the function, and sending back the result. The intermediate messages will be retained in the
    /// <see cref="ChatHistory"/> if an instance was provided.
    /// </remarks>
    public ToolCallBehavior? ToolCallBehavior
    {
        get => this._toolCallBehavior;

        set
        {
            this.ThrowIfFrozen();
            this._toolCallBehavior = value;
        }
    }

    /// <summary>
    /// A unique identifier representing your end-user, which can help OpenAI to monitor and detect abuse
    /// </summary>
    [JsonPropertyName("user")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? User
    {
        get => this._user;

        set
        {
            this.ThrowIfFrozen();
            this._user = value;
        }
    }

    /// <summary>
    /// Whether to return log probabilities of the output tokens or not.
    /// If true, returns the log probabilities of each output token returned in the `content` of `message`.
    /// </summary>
    [JsonPropertyName("logprobs")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonConverter(typeof(OptionalBoolJsonConverter))]
    public bool? Logprobs
    {
        get => this._logprobs;

        set
        {
            this.ThrowIfFrozen();
            this._logprobs = value;
        }
    }

    /// <summary>
    /// An integer specifying the number of most likely tokens to return at each token position, each with an associated log probability.
    /// </summary>
    [JsonPropertyName("top_logprobs")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? TopLogprobs
    {
        get => this._topLogprobs;

        set
        {
            this.ThrowIfFrozen();
            this._topLogprobs = value;
        }
    }

    /// <summary>
    /// Developer-defined tags and values used for filtering completions in the OpenAI dashboard.
    /// </summary>
    [JsonPropertyName("metadata")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IDictionary<string, string>? Metadata
    {
        get => this._metadata;

        set
        {
            this.ThrowIfFrozen();
            this._metadata = value;
        }
    }

    /// <summary>
    /// Whether or not to store the output of this chat completion request for use in the OpenAI model distillation or evals products.
    /// </summary>
    [JsonPropertyName("store")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonConverter(typeof(OptionalBoolJsonConverter))]
    public bool? Store
    {
        get => this._store;

        set
        {
            this.ThrowIfFrozen();
            this._store = value;
        }
    }

    /// <summary>
    /// An object to allow models to search the web for the latest information before generating a response.
    /// </summary>
    /// <remarks>
    /// Supported types are:
    /// <para>- <see cref="ChatWebSearchOptions"/> object;</para>
    /// <para>- <see cref="JsonElement"/>, which will be used to automatically deserialize into <see cref="ChatWebSearchOptions"/>.</para>
    /// <para>- <see cref="string"/>, which will be used to automatically deserialize into <see cref="ChatWebSearchOptions"/>.</para>
    /// <para>
    /// Currently, you need to use one of these models to use web search in Chat Completions:
    /// <list type="bullet">
    /// <item>gpt-4o-search-preview</item>
    /// <item>gpt-4o-mini-search-preview</item>
    /// </list>
    /// </para>
    /// </remarks>
    [Experimental("SKEXP0010")]
    [JsonPropertyName("web_search_options")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? WebSearchOptions
    {
        get => this._webSearchOptions;

        set
        {
            this.ThrowIfFrozen();
            this._webSearchOptions = value;
        }
    }

    /// <summary>
    /// Gets or sets the response modalities to use for the completion.
    /// </summary>
    /// <remarks>
    /// Specifies the modalities to use for the response. This can be represented in several ways:
    /// <list type="bullet">
    /// <item><description>As a <see cref="ChatResponseModalities"/> flags enum: <c>ChatResponseModalities.Text | ChatResponseModalities.Audio</c></description></item>
    /// <item><description>As an <see cref="IEnumerable{String}"/> of modality names: <c>new[] { "text", "audio" }</c></description></item>
    /// <item><description>As a <see cref="string"/> representation: <c>"Text, Audio"</c></description></item>
    /// <item><description>As a <see cref="JsonElement"/> containing either a string or an array of strings</description></item>
    /// </list>
    /// If this property is null, <see cref="ChatResponseModalities.Default"/> will be used, which typically means text-only responses.
    /// When audio is enabled, you should also set the <see cref="Audio"/> property.
    /// </remarks>
    [Experimental("SKEXP0010")]
    [JsonPropertyName("modalities")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? Modalities
    {
        get => this._responseModalities;

        set
        {
            this.ThrowIfFrozen();
            this._responseModalities = value;
        }
    }

    /// <summary>
    /// Gets or sets the audio options to use for the completion when audio modality is enabled.
    /// </summary>
    /// <remarks>
    /// Use this property to configure the output audio voice and format when the <see cref="Modalities"/> property includes audio.
    /// This can be represented in several ways:
    /// <list type="bullet">
    /// <item><description>As a <see cref="ChatAudioOptions"/> object: <c>new ChatAudioOptions(ChatOutputAudioVoice.Alloy, ChatOutputAudioFormat.Mp3)</c></description></item>
    /// <item><description>As a <see cref="JsonElement"/> containing the serialized audio options</description></item>
    /// <item><description>As a <see cref="string"/> containing the JSON representation of the audio options</description></item>
    /// </list>
    /// </remarks>
    [Experimental("SKEXP0010")]
    [JsonPropertyName("audio")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? Audio
    {
        get => this._audioOptions;

        set
        {
            this.ThrowIfFrozen();
            this._audioOptions = value;
        }
    }

    /// <inheritdoc/>
    public override void Freeze()
    {
        if (this.IsFrozen)
        {
            return;
        }

        base.Freeze();

        if (this._stopSequences is not null)
        {
            this._stopSequences = new ReadOnlyCollection<string>(this._stopSequences);
        }

        if (this._tokenSelectionBiases is not null)
        {
            this._tokenSelectionBiases = new ReadOnlyDictionary<int, int>(this._tokenSelectionBiases);
        }

        if (this._metadata is not null)
        {
            this._metadata = new ReadOnlyDictionary<string, string>(this._metadata);
        }
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return this.Clone<OpenAIPromptExecutionSettings>();
    }

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="executionSettings">Template configuration</param>
    /// <param name="defaultMaxTokens">Default max tokens</param>
    /// <returns>An instance of OpenAIPromptExecutionSettings</returns>
    public static OpenAIPromptExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings, int? defaultMaxTokens = null)
    {
        if (executionSettings is null)
        {
            return new OpenAIPromptExecutionSettings()
            {
                MaxTokens = defaultMaxTokens
            };
        }

        if (executionSettings is OpenAIPromptExecutionSettings settings)
        {
            return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);

        var openAIExecutionSettings = JsonSerializer.Deserialize<OpenAIPromptExecutionSettings>(json, JsonOptionsCache.ReadPermissive);

        // Restore the function choice behavior that lost internal state(list of function instances) during serialization/deserialization process.
        openAIExecutionSettings!.FunctionChoiceBehavior = executionSettings.FunctionChoiceBehavior;

        return openAIExecutionSettings;
    }

    /// <summary>
    /// Clone the settings object.
    /// </summary>
    /// <typeparam name="T">The type of the settings object to clone.</typeparam>
    /// <returns>A new instance of the settings object.</returns>
    protected internal T Clone<T>() where T : OpenAIPromptExecutionSettings, new()
    {
        return new T()
        {
            ModelId = this.ModelId,
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null,
            Temperature = this.Temperature,
            TopP = this.TopP,
            PresencePenalty = this.PresencePenalty,
            FrequencyPenalty = this.FrequencyPenalty,
            MaxTokens = this.MaxTokens,
            StopSequences = this.StopSequences is not null ? new List<string>(this.StopSequences) : null,
            Seed = this.Seed,
            ResponseFormat = this.ResponseFormat,
            TokenSelectionBiases = this.TokenSelectionBiases is not null ? new Dictionary<int, int>(this.TokenSelectionBiases) : null,
            ToolCallBehavior = this.ToolCallBehavior,
            FunctionChoiceBehavior = this.FunctionChoiceBehavior,
            User = this.User,
            ChatSystemPrompt = this.ChatSystemPrompt,
            ChatDeveloperPrompt = this.ChatDeveloperPrompt,
            Logprobs = this.Logprobs,
            TopLogprobs = this.TopLogprobs,
            Store = this.Store,
            Metadata = this.Metadata is not null ? new Dictionary<string, string>(this.Metadata) : null,
            ReasoningEffort = this.ReasoningEffort,
            WebSearchOptions = this.WebSearchOptions,
            Modalities = this.Modalities,
            Audio = this.Audio,
        };
    }

    #region private ================================================================================

    private object? _webSearchOptions;
    private object? _reasoningEffort;
    private double? _temperature;
    private double? _topP;
    private double? _presencePenalty;
    private double? _frequencyPenalty;
    private int? _maxTokens;
    private IList<string>? _stopSequences;
    private long? _seed;
    private object? _responseFormat;
    private IDictionary<int, int>? _tokenSelectionBiases;
    private ToolCallBehavior? _toolCallBehavior;
    private string? _user;
    private string? _chatSystemPrompt;
    private string? _chatDeveloperPrompt;
    private bool? _logprobs;
    private int? _topLogprobs;
    private bool? _store;
    private IDictionary<string, string>? _metadata;
    private object? _responseModalities;
    private object? _audioOptions;

    #endregion
}

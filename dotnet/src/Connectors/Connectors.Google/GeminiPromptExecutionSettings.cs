// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Google;

/// <summary>
/// Represents the settings for executing a prompt with the Gemini model.
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class GeminiPromptExecutionSettings : PromptExecutionSettings
{
    private double? _temperature;
    private double? _topP;
    private int? _topK;
    private int? _maxTokens;
    private int? _candidateCount;
    private IList<string>? _stopSequences;
    private bool? _audioTimestamp;
    private string? _responseMimeType;
    private object? _responseSchema;
    private string? _cachedContent;
    private IList<GeminiSafetySetting>? _safetySettings;
    private GeminiToolCallBehavior? _toolCallBehavior;
    private GeminiThinkingConfig? _thinkingConfig;

    /// <summary>
    /// Default max tokens for a text generation.
    /// </summary>
    public static int DefaultTextMaxTokens { get; } = 256;

    /// <summary>
    /// Temperature controls the randomness of the completion.
    /// The higher the temperature, the more random the completion.
    /// Range is 0.0 to 1.0.
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
    /// Gets or sets the value of the TopK property.
    /// The TopK property represents the maximum value of a collection or dataset.
    /// </summary>
    [JsonPropertyName("top_k")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? TopK
    {
        get => this._topK;
        set
        {
            this.ThrowIfFrozen();
            this._topK = value;
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
    /// The count of candidates. Possible values range from 1 to 8.
    /// </summary>
    [JsonPropertyName("candidate_count")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? CandidateCount
    {
        get => this._candidateCount;
        set
        {
            this.ThrowIfFrozen();
            this._candidateCount = value;
        }
    }

    /// <summary>
    /// Sequences where the completion will stop generating further tokens.
    /// Maximum number of stop sequences is 5.
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
    /// Represents a list of safety settings.
    /// </summary>
    [JsonPropertyName("safety_settings")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IList<GeminiSafetySetting>? SafetySettings
    {
        get => this._safetySettings;
        set
        {
            this.ThrowIfFrozen();
            this._safetySettings = value;
        }
    }

    /// <summary>
    /// Gets or sets the behavior for how tool calls are handled.
    /// </summary>
    /// <remarks>
    /// <list type="bullet">
    /// <item>To disable all tool calling, set the property to null (the default).</item>
    /// <item>
    /// To allow the model to request one of any number of functions, set the property to an
    /// instance returned from <see cref="GeminiToolCallBehavior.EnableFunctions"/>, called with
    /// a list of the functions available.
    /// </item>
    /// <item>
    /// To allow the model to request one of any of the functions in the supplied <see cref="Kernel"/>,
    /// set the property to <see cref="GeminiToolCallBehavior.EnableKernelFunctions"/> if the client should simply
    /// send the information about the functions and not handle the response in any special manner, or
    /// <see cref="GeminiToolCallBehavior.AutoInvokeKernelFunctions"/> if the client should attempt to automatically
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
    public GeminiToolCallBehavior? ToolCallBehavior
    {
        get => this._toolCallBehavior;

        set
        {
            this.ThrowIfFrozen();
            this._toolCallBehavior = value;
        }
    }

    /// <summary>
    /// Indicates if the audio response should include timestamps.
    /// if enabled, audio timestamp will be included in the request to the model.
    /// </summary>
    [JsonPropertyName("audio_timestamp")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    [JsonConverter(typeof(OptionalBoolJsonConverter))]
    public bool? AudioTimestamp
    {
        get => this._audioTimestamp;
        set
        {
            this.ThrowIfFrozen();
            this._audioTimestamp = value;
        }
    }

    /// <summary>
    /// The output response MIME type of the generated candidate text.
    /// The following MIME types are supported:
    /// 1. application/json: JSON response in the candidates.
    /// 2. text/plain (default): Plain text output.
    /// 3. text/x.enum: For classification tasks, output an enum value as defined in the response schema.
    /// </summary>
    [JsonPropertyName("response_mimetype")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? ResponseMimeType
    {
        get => this._responseMimeType;
        set
        {
            this.ThrowIfFrozen();
            this._responseMimeType = value;
        }
    }

    /// <summary>
    /// Optional. Output schema of the generated candidate text. Schemas must be a subset of the OpenAPI schema and can be objects, primitives or arrays.
    /// If set, a compatible responseMimeType must also be set. Compatible MIME types: application/json: Schema for JSON response.
    /// Refer to the https://ai.google.dev/gemini-api/docs/json-mode for more information.
    /// </summary>
    /// <remarks>
    /// Possible values are:
    /// <para>- <see cref="Type"/> which will be used to automatically generate a JSON schema.</para>
    /// <para>- <see cref="JsonElement"/> schema definition, which will be used as is.</para>
    /// <para>- <see cref="JsonNode"/> schema definition, which will be used as is.</para>
    /// <para>- <see cref="JsonDocument"/> schema definition, which will be used as is.</para>
    /// <para>- <see cref="object"/> object, where none of the above matches which the type will be used to automatically generate a JSON schema.</para>
    /// </remarks>
    [JsonPropertyName("response_schema")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? ResponseSchema
    {
        get => this._responseSchema;

        set
        {
            this.ThrowIfFrozen();
            this._responseSchema = value;
        }
    }

    /// <summary>
    /// Optional. The name of the cached content used as context to serve the prediction.
    /// Note: only used in explicit caching, where users can have control over caching (e.g. what content to cache) and enjoy guaranteed cost savings.
    /// Format: projects/{project}/locations/{location}/cachedContents/{cachedContent}
    /// </summary>
    [JsonPropertyName("cached_content")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? CachedContent
    {
        get => this._cachedContent;
        set
        {
            this.ThrowIfFrozen();
            this._cachedContent = value;
        }
    }

    /// <summary>
    /// Configuration for the thinking budget in Gemini 2.5.
    /// </summary>
    /// <remarks>
    /// This property is specific to Gemini 2.5 and similar experimental models.
    /// </remarks>
    [JsonPropertyName("thinking_config")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public GeminiThinkingConfig? ThinkingConfig
    {
        get => this._thinkingConfig;
        set
        {
            this.ThrowIfFrozen();
            this._thinkingConfig = value;
        }
    }

    /// <inheritdoc />
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

        if (this._safetySettings is not null)
        {
            this._safetySettings = new ReadOnlyCollection<GeminiSafetySetting>(this._safetySettings);
        }
    }

    /// <inheritdoc />
    public override PromptExecutionSettings Clone()
    {
        return new GeminiPromptExecutionSettings()
        {
            ModelId = this.ModelId,
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null,
            Temperature = this.Temperature,
            TopP = this.TopP,
            TopK = this.TopK,
            MaxTokens = this.MaxTokens,
            CandidateCount = this.CandidateCount,
            StopSequences = this.StopSequences is not null ? new List<string>(this.StopSequences) : null,
            SafetySettings = this.SafetySettings?.Select(setting => new GeminiSafetySetting(setting)).ToList(),
            ToolCallBehavior = this.ToolCallBehavior?.Clone(),
            AudioTimestamp = this.AudioTimestamp,
            ResponseMimeType = this.ResponseMimeType,
            ResponseSchema = this.ResponseSchema,
            ThinkingConfig = this.ThinkingConfig?.Clone()
        };
    }

    /// <summary>
    /// Converts a <see cref="PromptExecutionSettings"/> object to a <see cref="GeminiPromptExecutionSettings"/> object.
    /// </summary>
    /// <param name="executionSettings">The <see cref="PromptExecutionSettings"/> object to convert.</param>
    /// <returns>
    /// The converted <see cref="GeminiPromptExecutionSettings"/> object. If <paramref name="executionSettings"/> is null,
    /// a new instance of <see cref="GeminiPromptExecutionSettings"/> is returned. If <paramref name="executionSettings"/>
    /// is already a <see cref="GeminiPromptExecutionSettings"/> object, it is casted and returned. Otherwise, the method
    /// tries to deserialize <paramref name="executionSettings"/> to a <see cref="GeminiPromptExecutionSettings"/> object.
    /// If deserialization is successful, the converted object is returned. If deserialization fails or the converted object
    /// is null, an <see cref="ArgumentException"/> is thrown.
    /// </returns>
    public static GeminiPromptExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        switch (executionSettings)
        {
            case null:
                return new GeminiPromptExecutionSettings() { MaxTokens = DefaultTextMaxTokens };
            case GeminiPromptExecutionSettings settings:
                return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);
        return JsonSerializer.Deserialize<GeminiPromptExecutionSettings>(json, JsonOptionsCache.ReadPermissive)!;
    }
}

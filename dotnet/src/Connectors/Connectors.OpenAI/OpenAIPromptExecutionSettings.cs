// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Execution settings for an OpenAI completion request.
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class OpenAIPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Temperature controls the randomness of the completion.
    /// The higher the temperature, the more random the completion.
    /// Default is 1.0.
    /// </summary>
    [JsonPropertyName("temperature")]
    public double Temperature
    {
        get => this._temperature;
        set
        {
            this._temperature = value;
            this.ExtensionData!["temperature"] = value;
        }
    }

    /// <summary>
    /// TopP controls the diversity of the completion.
    /// The higher the TopP, the more diverse the completion.
    /// Default is 1.0.
    /// </summary>
    [JsonPropertyName("top_p")]
    public double TopP
    {
        get => this._top_p;
        set
        {
            this._top_p = value;
            this.ExtensionData!["top_p"] = value;
        }
    }

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on whether they appear in the text so far, increasing the
    /// model's likelihood to talk about new topics.
    /// </summary>
    [JsonPropertyName("presence_penalty")]
    public double PresencePenalty
    {
        get => this._presence_penalty;
        set
        {
            this._presence_penalty = value;
            this.ExtensionData!["presence_penalty"] = value;
        }
    }

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens
    /// based on their existing frequency in the text so far, decreasing
    /// the model's likelihood to repeat the same line verbatim.
    /// </summary>
    [JsonPropertyName("frequency_penalty")]
    public double FrequencyPenalty
    {
        get => this._frequency_penalty;
        set
        {
            this._frequency_penalty = value;
            this.ExtensionData!["frequency_penalty"] = value;
        }
    }

    /// <summary>
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    [JsonPropertyName("max_tokens")]
    public int? MaxTokens
    {
        get => this._maxTokens;
        set
        {
            this._maxTokens = value;

            if (value is null)
            {
                this.ExtensionData!.Remove("max_tokens");
            }
            else
            {
                this.ExtensionData!["max_tokens"] = value;
            }
        }
    }

    /// <summary>
    /// Sequences where the completion will stop generating further tokens.
    /// </summary>
    [JsonPropertyName("stop_sequences")]
    public IList<string>? StopSequences
    {
        get => this._stop_sequences;
        set
        {
            this._stop_sequences = value;

            if (value is null)
            {
                this.ExtensionData!.Remove("stop_sequences");
            }
            else
            {
                this.ExtensionData!["stop_sequences"] = value;
            }
        }
    }

    /// <summary>
    /// How many completions to generate for each prompt. Default is 1.
    /// Note: Because this parameter generates many completions, it can quickly consume your token quota.
    /// Use carefully and ensure that you have reasonable settings for max_tokens and stop.
    /// </summary>
    [JsonPropertyName("results_per_prompt")]
    public int ResultsPerPrompt
    {
        get => this._results_per_prompt;
        set
        {
            this._results_per_prompt = value;
            this.ExtensionData!["results_per_prompt"] = value;
        }
    }

    /// <summary>
    /// If specified, the system will make a best effort to sample deterministically such that repeated requests with the
    /// same seed and parameters should return the same result. Determinism is not guaranteed.
    /// </summary>
    [Experimental("SKEXP0013")]
    [JsonPropertyName("seed")]
    public long? Seed
    {
        get => this._seed;
        set
        {
            this._seed = value;

            if (value is null)
            {
                this.ExtensionData!.Remove("seed");
            }
            else
            {
                this.ExtensionData!["seed"] = value;
            }
        }
    }

    /// <summary>
    /// Gets or sets the response format to use for the completion.
    /// </summary>
    [Experimental("SKEXP0013")]
    [JsonPropertyName("response_format")]
    public object? ResponseFormat
    {
        get => this._response_format;
        set
        {
            this._response_format = value;

            if (value is null)
            {
                this.ExtensionData!.Remove("response_format");
            }
            else
            {
                this.ExtensionData!["response_format"] = value;
            }
        }
    }

    /// <summary>
    /// The system prompt to use when generating text using a chat model.
    /// Defaults to "Assistant is a large language model."
    /// </summary>
    [JsonPropertyName("chat_system_prompt")]
    public string ChatSystemPrompt
    {
        get => this._chatSystemPrompt;
        set
        {
            if (string.IsNullOrWhiteSpace(value))
            {
                value = DefaultChatSystemPrompt;
            }
            this._chatSystemPrompt = value;
            this.ExtensionData!["chat_system_prompt"] = value;
        }
    }

    /// <summary>
    /// Modify the likelihood of specified tokens appearing in the completion.
    /// </summary>
    [JsonPropertyName("token_selection_biases")]
    public IDictionary<int, int>? TokenSelectionBiases { get; set; }

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
    public ToolCallBehavior? ToolCallBehavior { get; set; }

    /// <summary>
    /// Default constructor.
    /// </summary>
    public OpenAIPromptExecutionSettings()
    {
        this.ChatSystemPrompt = DefaultChatSystemPrompt;
    }

    /// <summary>
    /// Default value for chat system property.
    /// </summary>
    internal static string DefaultChatSystemPrompt { get; } = "Assistant is a large language model.";

    /// <summary>
    /// Default max tokens for a text generation
    /// </summary>
    internal static int DefaultTextMaxTokens { get; } = 256;

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
        if (openAIExecutionSettings is not null)
        {
            return openAIExecutionSettings;
        }

        throw new ArgumentException($"Invalid execution settings, cannot convert to {nameof(OpenAIPromptExecutionSettings)}", nameof(executionSettings));
    }

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="executionSettings">Template configuration</param>
    /// <param name="defaultMaxTokens">Default max tokens</param>
    /// <returns>An instance of OpenAIPromptExecutionSettings</returns>
    public static OpenAIPromptExecutionSettings FromExecutionSettingsWithData(PromptExecutionSettings? executionSettings, int? defaultMaxTokens = null)
    {
        var settings = FromExecutionSettings(executionSettings, defaultMaxTokens);

        if (settings.StopSequences?.Count == 0)
        {
            // Azure OpenAI WithData API does not allow to send empty array of stop sequences
            // Gives back "Validation error at #/stop/str: Input should be a valid string\nValidation error at #/stop/list[str]: List should have at least 1 item after validation, not 0"
            settings.StopSequences = null;
        }

        return settings;
    }

    #region private ================================================================================

    private double _temperature = 1;
    private double _top_p = 1;
    private double _presence_penalty;
    private double _frequency_penalty;
    private int? _maxTokens;
    private IList<string>? _stop_sequences;
    private int _results_per_prompt = 1;
    private long? _seed;
    private object? _response_format;
    private IDictionary<int, int>? _token_selection_biases;
    private string _chatSystemPrompt = DefaultChatSystemPrompt;

    #endregion
}

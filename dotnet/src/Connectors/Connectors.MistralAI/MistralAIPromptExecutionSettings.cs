// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.MistralAI;

/// <summary>
/// Mistral Execution Settings.
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class MistralAIPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Default: 0.7
    /// What sampling temperature to use, between 0.0 and 1.0. Higher values like 0.8 will make the output more random, while lower values like 0.2 will make it more focused and deterministic.
    /// </summary>
    /// <remarks>
    /// We generally recommend altering this or top_p but not both.
    /// </remarks>
    [JsonPropertyName("temperature")]
    public double Temperature
    {
        get => this._temperature;

        set
        {
            this.ThrowIfFrozen();
            this._temperature = value;
        }
    }

    /// <summary>
    /// Default: 1
    /// Nucleus sampling, where the model considers the results of the tokens with top_p probability mass.So 0.1 means only the tokens comprising the top 10% probability mass are considered.
    /// </summary>
    /// <remarks>
    /// We generally recommend altering this or temperature but not both.
    /// </remarks>
    [JsonPropertyName("top_p")]
    public double TopP
    {
        get => this._topP;

        set
        {
            this.ThrowIfFrozen();
            this._topP = value;
        }
    }

    /// <summary>
    /// Default: null
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    /// <remarks>
    /// The token count of your prompt plus max_tokens cannot exceed the model's context length.
    /// </remarks>
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
    /// Default: false
    /// Whether to inject a safety prompt before all conversations.
    /// </summary>
    [JsonPropertyName("safe_prompt")]
    public bool SafePrompt
    {
        get => this._safePrompt;

        set
        {
            this.ThrowIfFrozen();
            this._safePrompt = value;
        }
    }

    /// <summary>
    /// Default: null
    /// The seed to use for random sampling. If set, different calls will generate deterministic results.
    /// </summary>
    [JsonPropertyName("random_seed")]
    public int? RandomSeed
    {
        get => this._randomSeed;

        set
        {
            this.ThrowIfFrozen();
            this._randomSeed = value;
        }
    }

    /// <summary>
    /// The API version to use.
    /// </summary>
    [JsonPropertyName("api_version")]
    public string ApiVersion
    {
        get => this._apiVersion;

        set
        {
            this.ThrowIfFrozen();
            this._apiVersion = value;
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
    /// instance returned from <see cref="MistralAIToolCallBehavior.EnableFunctions"/>, called with
    /// a list of the functions available.
    /// </item>
    /// <item>
    /// To allow the model to request one of any of the functions in the supplied <see cref="Kernel"/>,
    /// set the property to <see cref="MistralAIToolCallBehavior.EnableKernelFunctions"/> if the client should simply
    /// send the information about the functions and not handle the response in any special manner, or
    /// <see cref="MistralAIToolCallBehavior.AutoInvokeKernelFunctions"/> if the client should attempt to automatically
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
    public MistralAIToolCallBehavior? ToolCallBehavior
    {
        get => this._toolCallBehavior;

        set
        {
            this.ThrowIfFrozen();
            this._toolCallBehavior = value;
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
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return new MistralAIPromptExecutionSettings()
        {
            ModelId = this.ModelId,
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null,
            Temperature = this.Temperature,
            TopP = this.TopP,
            MaxTokens = this.MaxTokens,
            SafePrompt = this.SafePrompt,
            RandomSeed = this.RandomSeed,
            ApiVersion = this.ApiVersion,
            ToolCallBehavior = this.ToolCallBehavior,
        };
    }

    /// <summary>
    /// Create a new settings object with the values from another settings object.
    /// </summary>
    /// <param name="executionSettings">Template configuration</param>
    /// <returns>An instance of MistralAIPromptExecutionSettings</returns>
    public static MistralAIPromptExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        if (executionSettings is null)
        {
            return new MistralAIPromptExecutionSettings()
            {
            };
        }

        if (executionSettings is MistralAIPromptExecutionSettings settings)
        {
            return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);

        var mistralExecutionSettings = JsonSerializer.Deserialize<MistralAIPromptExecutionSettings>(json, JsonOptionsCache.ReadPermissive);
        return mistralExecutionSettings!;
    }

    #region private ================================================================================

    private double _temperature = 0.7;
    private double _topP = 1;
    private int? _maxTokens;
    private bool _safePrompt = false;
    private int? _randomSeed;
    private string _apiVersion = "v1";
    private MistralAIToolCallBehavior? _toolCallBehavior;

    #endregion
}

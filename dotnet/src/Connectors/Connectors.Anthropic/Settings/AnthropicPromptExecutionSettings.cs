// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Anthropic prompt execution settings.
/// Extends the base PromptExecutionSettings with Anthropic-specific options.
/// </summary>
/// <remarks>
/// <para><strong>FunctionChoice behavior differences from OpenAI:</strong></para>
/// <list type="bullet">
/// <item><description><c>FunctionChoice.Auto</c>: Model decides whether to call functions (maps to Anthropic's <c>tool_choice=auto</c>)</description></item>
/// <item><description><c>FunctionChoice.Required</c>: Model must call a function (maps to Anthropic's <c>tool_choice=any</c>)</description></item>
/// <item><description><c>FunctionChoice.None</c>: <strong>Tools are not sent to the API</strong>. Unlike OpenAI where
/// <c>tool_choice=none</c> sends tools but prevents calling them, Anthropic does not support this mode.
/// The model will not be aware of available functions when <c>FunctionChoice.None</c> is set.</description></item>
/// </list>
/// </remarks>
[Experimental("SKEXP0001")]
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class AnthropicPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Temperature controls randomness in the response.
    /// Range: 0.0 to 1.0. Higher values make output more random.
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
    /// Maximum number of tokens to generate in the response.
    /// Anthropic requires this to be set explicitly. Default: 32000.
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
    /// Top-p sampling parameter. Alternative to temperature.
    /// Range: 0.0 to 1.0. Lower values make output more focused.
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
    /// Top-K sampling parameter. Only sample from the top K options for each token.
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
    /// Custom stop sequences where the API will stop generating further tokens.
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
    /// Function choice behavior for tool calling.
    /// </summary>
    [JsonIgnore]
    public new FunctionChoiceBehavior? FunctionChoiceBehavior
    {
        get => this._functionChoiceBehavior;
        set
        {
            this.ThrowIfFrozen();
            this._functionChoiceBehavior = value;
        }
    }

    // Private backing fields
    private double? _temperature;
    private int? _maxTokens;
    private double? _topP;
    private int? _topK;
    private IList<string>? _stopSequences;
    private FunctionChoiceBehavior? _functionChoiceBehavior;

    /// <summary>
    /// Initializes a new instance of the <see cref="AnthropicPromptExecutionSettings"/> class.
    /// </summary>
    public AnthropicPromptExecutionSettings()
    {
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
            this._stopSequences = new ReadOnlyCollection<string>(this._stopSequences is List<string> list ? list : new List<string>(this._stopSequences));
        }
    }

    /// <inheritdoc/>
    public override PromptExecutionSettings Clone()
    {
        return new AnthropicPromptExecutionSettings
        {
            ModelId = this.ModelId,
            ServiceId = this.ServiceId,
            ExtensionData = this.ExtensionData is not null ? new Dictionary<string, object>(this.ExtensionData) : null,
            Temperature = this._temperature,
            MaxTokens = this._maxTokens,
            TopP = this._topP,
            TopK = this._topK,
            StopSequences = this._stopSequences is not null ? new List<string>(this._stopSequences) : null,
            FunctionChoiceBehavior = this._functionChoiceBehavior
        };
    }

    /// <summary>
    /// Creates a new instance of <see cref="AnthropicPromptExecutionSettings"/> from an existing <see cref="PromptExecutionSettings"/>.
    /// </summary>
    /// <remarks>
    /// This method uses JSON serialization to convert settings from other providers (e.g., OpenAI) to Anthropic settings.
    /// Properties with matching JSON names (temperature, max_tokens, top_p, stop_sequences) are automatically mapped.
    /// FunctionChoiceBehavior is explicitly preserved as it cannot be serialized.
    /// </remarks>
    /// <param name="executionSettings">The existing execution settings to convert.</param>
    /// <returns>An <see cref="AnthropicPromptExecutionSettings"/> instance.</returns>
    public static AnthropicPromptExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        switch (executionSettings)
        {
            case null:
                return new AnthropicPromptExecutionSettings();
            case AnthropicPromptExecutionSettings settings:
                return settings;
        }

        // Use JSON serialization to convert from other settings types (e.g., OpenAIPromptExecutionSettings).
        // This automatically maps properties with matching JSON names.
        var json = JsonSerializer.Serialize(executionSettings);
        var anthropicSettings = JsonSerializer.Deserialize<AnthropicPromptExecutionSettings>(json, JsonOptionsCache.ReadPermissive)!;

        // Restore FunctionChoiceBehavior that is lost during serialization (it's marked with [JsonIgnore])
        anthropicSettings.FunctionChoiceBehavior = executionSettings.FunctionChoiceBehavior;

        return anthropicSettings;
    }
}

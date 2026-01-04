// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Anthropic prompt execution settings.
/// Extends the base PromptExecutionSettings with Anthropic-specific options.
/// </summary>
/// <remarks>
/// <para><strong>FunctionChoiceBehavior mapping to Anthropic tool_choice:</strong></para>
/// <list type="bullet">
/// <item><description><see cref="FunctionChoiceBehavior.Auto"/>: Model decides whether to call functions (maps to <c>tool_choice=auto</c>)</description></item>
/// <item><description><see cref="FunctionChoiceBehavior.Required"/>: Model must call a function (maps to <c>tool_choice=any</c>)</description></item>
/// <item><description><see cref="FunctionChoiceBehavior.None"/>: Tools are sent but model is instructed not to call any (maps to <c>tool_choice=none</c>).
/// This matches OpenAI semantics where the model is aware of available functions but will not invoke them.</description></item>
/// </list>
/// </remarks>
[Experimental("SKEXP0001")]
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class AnthropicPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Temperature controls randomness in the response.
    /// Range: 0.0 to 1.0. Defaults to 1.0. Higher values make output more random.
    /// Use lower values for analytical/multiple choice, higher for creative tasks.
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
    /// Anthropic requires this parameter. The connector applies a default of 32000 if not specified.
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
    /// The system prompt to use when generating text using a chat model.
    /// When set, this prompt is automatically inserted at the beginning of the chat history
    /// if no system message is already present.
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

    // Note: FunctionChoiceBehavior is inherited from PromptExecutionSettings.
    // We do NOT shadow it with 'new' because that breaks polymorphism -
    // when ToChatOptions() reads settings.FunctionChoiceBehavior via a base class reference,
    // it would get null instead of the actual value.

    // Private backing fields
    private double? _temperature;
    private int? _maxTokens;
    private double? _topP;
    private int? _topK;
    private IList<string>? _stopSequences;
    private string? _chatSystemPrompt;

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
            ChatSystemPrompt = this._chatSystemPrompt,
            FunctionChoiceBehavior = this.FunctionChoiceBehavior
        };
    }

    /// <inheritdoc/>
    protected override ChatHistory PrepareChatHistoryForRequest(ChatHistory chatHistory)
    {
        // Insert system prompt at the beginning of the chat history if set and not already present.
        if (!string.IsNullOrWhiteSpace(this.ChatSystemPrompt) && !chatHistory.Any(m => m.Role == AuthorRole.System))
        {
            chatHistory.Insert(0, new ChatMessageContent(AuthorRole.System, this.ChatSystemPrompt));
        }

        return chatHistory;
    }

    /// <summary>
    /// Creates a new instance of <see cref="AnthropicPromptExecutionSettings"/> from an existing <see cref="PromptExecutionSettings"/>.
    /// </summary>
    /// <remarks>
    /// This method uses JSON serialization to convert settings from other providers (e.g., OpenAI) to Anthropic settings.
    /// Properties with matching JSON names (temperature, max_tokens, top_p, top_k, stop_sequences) are automatically mapped.
    /// FunctionChoiceBehavior is explicitly preserved as it cannot be serialized.
    /// </remarks>
    /// <param name="executionSettings">The existing execution settings to convert.</param>
    /// <param name="defaultMaxTokens">Default max tokens to use when not specified in settings. Anthropic requires this parameter.</param>
    /// <returns>An <see cref="AnthropicPromptExecutionSettings"/> instance.</returns>
    public static AnthropicPromptExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings, int? defaultMaxTokens = null)
    {
        switch (executionSettings)
        {
            case null:
                return new AnthropicPromptExecutionSettings
                {
                    MaxTokens = defaultMaxTokens
                };
            case AnthropicPromptExecutionSettings settings:
                return settings;
        }

        // Use JSON serialization to convert from other settings types (e.g., OpenAIPromptExecutionSettings).
        // This automatically maps properties with matching JSON names.
        // Important: Serialize as object to ensure derived type properties are included, not just base class.
        var json = JsonSerializer.Serialize<object>(executionSettings);
        var anthropicSettings = JsonSerializer.Deserialize<AnthropicPromptExecutionSettings>(json, JsonOptionsCache.ReadPermissive)!;

        // Apply default max tokens if not set in source settings
        anthropicSettings.MaxTokens ??= defaultMaxTokens;

        // Restore FunctionChoiceBehavior that loses internal state during serialization/deserialization process.
        anthropicSettings.FunctionChoiceBehavior = executionSettings.FunctionChoiceBehavior;

        return anthropicSettings;
    }
}

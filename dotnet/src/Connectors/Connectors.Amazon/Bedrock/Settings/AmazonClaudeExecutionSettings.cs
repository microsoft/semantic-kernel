// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Connectors.Amazon;

/// <summary>
/// Prompt execution settings for Anthropic Claude Text Generation
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class AmazonClaudeExecutionSettings : PromptExecutionSettings
{
    private int _maxTokensToSample;
    private List<string>? _stopSequences;
    private float? _temperature;
    private float? _topP;
    private int? _topK;
    private bool _enableSystemCaching;
    private bool _enableMessageCaching;
    private int? _systemCacheBreakpoint;
    private List<int>? _messageCacheBreakpoints;

    /// <summary>
    /// Default max tokens for a text generation.
    /// </summary>
    private const int DefaultTextMaxTokens = 200;

    /// <summary>
    /// (Required) The maximum number of tokens to generate before stopping. We recommend a limit of 4,000 tokens for optimal performance.
    /// </summary>
    [JsonPropertyName("max_tokens_to_sample")]
    public int MaxTokensToSample
    {
        get => this._maxTokensToSample;
        set
        {
            this.ThrowIfFrozen();
            this._maxTokensToSample = value;
        }
    }

    /// <summary>
    /// (Optional) Sequences that will cause the model to stop generating. Anthropic Claude models stop on "\n\nHuman:", and may include additional built-in stop sequences in the future.Use the stop_sequences inference parameter to include additional strings that will signal the model to stop generating text.
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
    /// (Optional) The amount of randomness injected into the response. Use a value closer to 0 for analytical / multiple choice, and a value closer to 1 for creative and generative tasks.
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
    /// (Optional) Use nucleus sampling. In nucleus sampling, Anthropic Claude computes the cumulative distribution over all the options for each subsequent token in decreasing probability order and cuts it off once it reaches a particular probability specified by top_p.You should alter either temperature or top_p, but not both.
    /// </summary>
    [JsonPropertyName("top_p")]
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
    /// (Optional) Only sample from the top K options for each subsequent token. Use top_k to remove long tail low probability responses.
    /// </summary>
    [JsonPropertyName("top_k")]
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
    /// (Optional) Enables prompt caching for system messages. When true, system messages will be cached for reuse across requests.
    /// Requires at least 1,024 tokens in system content for Claude 3.7 Sonnet, 2,048 tokens for Claude 3.5 Haiku.
    /// Cache expires after 5 minutes of inactivity.
    /// </summary>
    [JsonPropertyName("enable_system_caching")]
    public bool EnableSystemCaching
    {
        get => this._enableSystemCaching;
        set
        {
            this.ThrowIfFrozen();
            this._enableSystemCaching = value;
        }
    }

    /// <summary>
    /// (Optional) Enables prompt caching for message content. When true, messages up to specified breakpoints will be cached.
    /// Use with MessageCacheBreakpoints to control where cache boundaries are placed.
    /// </summary>
    [JsonPropertyName("enable_message_caching")]
    public bool EnableMessageCaching
    {
        get => this._enableMessageCaching;
        set
        {
            this.ThrowIfFrozen();
            this._enableMessageCaching = value;
        }
    }

    /// <summary>
    /// (Optional) Specifies the message index where system cache breakpoint should be placed.
    /// Only used when EnableSystemCaching is true. If not specified, cache breakpoint will be placed after all system content.
    /// </summary>
    [JsonPropertyName("system_cache_breakpoint")]
    public int? SystemCacheBreakpoint
    {
        get => this._systemCacheBreakpoint;
        set
        {
            this.ThrowIfFrozen();
            this._systemCacheBreakpoint = value;
        }
    }

    /// <summary>
    /// (Optional) List of message indices where cache breakpoints should be placed.
    /// Only used when EnableMessageCaching is true. Maximum of 2 cache breakpoints allowed for messages.
    /// Each breakpoint must meet minimum token requirements (1,024+ tokens for Sonnet, 2,048+ for Haiku).
    /// </summary>
    [JsonPropertyName("message_cache_breakpoints")]
    public List<int>? MessageCacheBreakpoints
    {
        get => this._messageCacheBreakpoints;
        set
        {
            this.ThrowIfFrozen();
            this._messageCacheBreakpoints = value;
        }
    }

    /// <summary>
    /// Converts PromptExecutionSettings to ClaudeExecutionSettings
    /// </summary>
    /// <param name="executionSettings">The Kernel standard PromptExecutionSettings.</param>
    /// <returns>Model specific execution settings.</returns>
    public static AmazonClaudeExecutionSettings FromExecutionSettings(PromptExecutionSettings? executionSettings)
    {
        switch (executionSettings)
        {
            case null:
                return new AmazonClaudeExecutionSettings { MaxTokensToSample = DefaultTextMaxTokens };
            case AmazonClaudeExecutionSettings settings:
                return settings;
        }

        var json = JsonSerializer.Serialize(executionSettings);
        return JsonSerializer.Deserialize<AmazonClaudeExecutionSettings>(json, JsonOptionsCache.ReadPermissive)!;
    }
}

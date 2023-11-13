// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.Anthropic;

/// <summary>
/// A request to Anthropic's Completion API endpoint.
/// </summary>
public class AnthropicRequest
{
    private readonly AnthropicRequestSettings _settings;

    /// <summary>
    /// Creates an instance of this class
    /// </summary>
    /// <param name="settings">The settings to use for this request.</param>
    /// <param name="prompt">The prompt that you want Claude to complete.</param>
    /// <param name="stream">Whether or not to stream the response</param>
    public AnthropicRequest(AnthropicRequestSettings? settings = null, string? prompt = null, bool? stream = null)
    {
        this._settings = settings ?? new AnthropicRequestSettings();
        this.Prompt = prompt ?? string.Empty;
        this.Stream = stream ?? false;
    }

    /// <summary>
    /// The model that will complete your prompt.
    /// </summary>
    /// <remarks>
    /// As we improve Claude, we develop new versions of it that you can query. This parameter controls which version of
    /// Claude answers your request. Right now we are offering two model families: Claude, and Claude Instant. You can
    /// use them by setting model to "claude-2" or "claude-instant-1", respectively. See models for additional details.
    /// </remarks>
    [JsonPropertyName("model")]
    public string Model => this._settings.ModelId ?? "claude-2";

    /// <summary>
    /// The prompt that you want Claude to complete.
    /// </summary>
    [JsonPropertyName("prompt")]
    public string Prompt { get; } = string.Empty;

    /// <summary>
    /// Whether to incrementally stream the response using server-sent events.
    /// </summary>
    [JsonPropertyName("stream")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public bool Stream { get; }

    /// <summary>
    /// The maximum number of tokens to generate before stopping.
    /// </summary>
    /// <remarks>
    /// Note that our models may stop before reaching this maximum. This parameter only specifies the absolute maximum
    /// number of tokens to generate.
    /// </remarks>
    [JsonPropertyName("max_tokens_to_sample")]
    public int MaxTokensToSample => this._settings.MaxTokensToSample;

    /// <summary>
    /// Sequences that will cause the model to stop generating completion text.
    /// </summary>
    /// <remarks>
    /// Our models stop on "\n\nHuman:", and may include additional built-in stop sequences in the future. By providing
    /// the stop_sequences parameter, you may include additional strings that will cause the model to stop generating.
    /// </remarks>
    [JsonPropertyName("stop_sequences")]
    public IList<string> StopSequences => this._settings.StopSequences;

    /// <summary>
    /// Amount of randomness injected into the response.
    /// </summary>
    /// <remarks>
    /// Defaults to 1. Ranges from 0 to 1. Use temp closer to 0 for analytical / multiple choice, and closer to 1 for
    /// creative and generative tasks.
    /// </remarks>
    [JsonPropertyName("temperature")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? Temperature => this._settings.Temperature;

    /// <summary>
    /// Use nucleus sampling.
    /// </summary>
    /// <remarks>
    /// In nucleus sampling, we compute the cumulative distribution over all the options for each subsequent token in
    /// decreasing probability order and cut it off once it reaches a particular probability specified by top_p. You
    /// should either alter temperature or top_p, but not both.
    /// </remarks>
    [JsonPropertyName("top_p")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public double? TopP => this._settings.TopP;

    /// <summary>
    /// An object describing metadata about the request.
    /// </summary>
    [JsonPropertyName("metadata")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public IReadOnlyDictionary<string, object>? Metadata => this._settings.ExtensionData;
}

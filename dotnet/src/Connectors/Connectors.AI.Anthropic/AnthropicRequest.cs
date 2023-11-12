// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.Anthropic;

/// <summary>
/// A request to Anthropic's Completion API endpoint.
/// </summary>
public class AnthropicRequest : AnthropicRequestSettings
{
    private string _model = "claude-2";

    /// <summary>
    /// Creates an instance of this class
    /// </summary>
    public AnthropicRequest()
    {
    }

    /// <summary>
    /// Creates an instance of this class
    /// </summary>
    /// <param name="settings">The settings to use for this request.</param>
    public AnthropicRequest(AnthropicRequestSettings settings) : this()
    {
        this.MaxTokensToSample = settings.MaxTokensToSample;
        this.StopSequences = settings.StopSequences;
        this.Temperature = settings.Temperature;
        this.TopP = settings.TopP;
        this.TopK = settings.TopK;
        this.Metadata = settings.Metadata;
    }

    /// <summary>
    /// Creates an instance of this class
    /// </summary>
    /// <param name="settings">The settings to use for this request.</param>
    /// <param name="model">The model that will complete your prompt.</param>
    /// <param name="prompt">The prompt that you want Claude to complete.</param>
    /// <param name="stream">Whether or not to stream the response</param>
    public AnthropicRequest(AnthropicRequestSettings settings, string model, string prompt, bool stream) : this(settings)
    {
        this.Model = model;
        this.Prompt = prompt;
        this.Stream = stream;
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
    public string Model
    {
        get => this._model;
        set
        {
            if (value != "claude-2" && value != "claude-instant-1") throw new ArgumentOutOfRangeException(nameof(value), value, "Model must be claude-2 or claude-instant-1.");
            this._model = value;
        }
    }

    /// <summary>
    /// The prompt that you want Claude to complete.
    /// </summary>
    [JsonPropertyName("prompt")]
    public string Prompt { get; set; } = string.Empty;

    /// <summary>
    /// Whether to incrementally stream the response using server-sent events.
    /// </summary>
    [JsonPropertyName("stream")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingDefault)]
    public bool Stream { get; set; }
}

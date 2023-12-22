#region HEADER
// Copyright (c) Microsoft. All rights reserved.
#endregion

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Gemini.Settings;

/// <summary>
/// Represents the settings for executing a prompt with the Gemini model.
/// </summary>
[JsonNumberHandling(JsonNumberHandling.AllowReadingFromString)]
public sealed class GeminiPromptExecutionSettings : PromptExecutionSettings
{
    /// <summary>
    /// Temperature controls the randomness of the completion.
    /// The higher the temperature, the more random the completion.
    /// Default is 1.0.
    /// </summary>
    public double Temperature { get; set; } = 1;

    /// <summary>
    /// TopP controls the diversity of the completion.
    /// The higher the TopP, the more diverse the completion.
    /// Default is 0.95.
    /// </summary>
    public double TopP { get; set; } = 0.95;

    /// <summary>
    /// Gets or sets the value of the TopK property.
    /// The TopK property represents the maximum value of a collection or dataset.
    /// The default value is 50.
    /// </summary>
    public double TopK { get; set; } = 50;

    /// <summary>
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    public int? MaxTokens { get; set; }

    /// <summary>
    /// Sequences where the completion will stop generating further tokens.
    /// </summary>
    public IList<string>? StopSequences { get; set; }

    /// <summary>
    /// Represents a list of safety settings.
    /// </summary>
    public IList<SafetySetting>? SafetySettings { get; set; }
}

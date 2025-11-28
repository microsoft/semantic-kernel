// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google;

/// <summary>
/// GeminiThinkingConfig class
/// </summary>
public class GeminiThinkingConfig
{
    /// <summary>The thinking budget parameter gives the model guidance on how many thinking tokens it can use for its thinking process.</summary>
    /// <remarks>
    /// <para>A greater number of tokens is typically associated with more detailed thinking, which is needed for solving more complex tasks.
    /// thinkingBudget must be an integer in the range 0 to 24576. Setting the thinking budget to 0 disables thinking.
    /// Budgets from 1 to 1024 tokens will be set to 1024.
    /// </para>
    /// This parameter is specific to Gemini 2.5 and similar experimental models.
    /// If no ThinkingBudget is explicitly set, the API default (likely 0) will be used
    /// </remarks>
    [Obsolete("ThinkingBudget is deprecated in Gemini 3.0. Use ThinkingLevel instead.")]
    [JsonPropertyName("thinking_budget")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? ThinkingBudget { get; set; }

    /// <summary>The thinking level parameter specifies the amount of thinking the model should use for its thinking process.</summary>
    /// <remarks>
    /// <para>Possible values are "none", "low", "medium", and "high". The default is "medium".</para>
    /// This parameter is specific to Gemini 3.0 and later models.
    /// </remarks>
    [JsonPropertyName("thinking_level")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? ThinkingLevel { get; set; }

    /// <summary>
    /// Clones this instance.
    /// </summary>
    /// <returns></returns>
    public GeminiThinkingConfig Clone()
    {
        return (GeminiThinkingConfig)this.MemberwiseClone();
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google;

/// <summary>
/// GeminiThinkingConfig class
/// </summary>
public class GeminiThinkingConfig
{
    private int? _thinkingBudget;

    /// <summary>
    /// The thinking budget parameter gives the model guidance on how many thinking tokens it can use for its thinking process.
    /// A greater number of tokens is typically associated with more detailed thinking, which is needed for solving more complex tasks.
    /// thinkingBudget must be an integer in the range 0 to 24576. Setting the thinking budget to 0 disables thinking.
    /// Budgets from 1 to 1024 tokens will be set to 1024.
    /// </summary>
    /// <remarks>This parameter is specific to Gemini 2.5 and similar experimental models.</remarks>
    [JsonPropertyName("thinkingBudget")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? ThinkingBudget
    {
        get => this._thinkingBudget;
        set
        {
            this._thinkingBudget = value == 0 ? 0 : (value < 1024 ? 1024 : value);
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="GeminiThinkingConfig"/> class.
    /// For Gemini 2.5, if no ThinkingBudget is explicitly set, the API default (likely 0) will be used.
    /// You can explicitly set a value here if needed.
    /// </summary>
    public GeminiThinkingConfig()
    {
        this._thinkingBudget = 0;
    }

    /// <summary>
    /// Clones this instance.
    /// </summary>
    /// <returns></returns>
    public GeminiThinkingConfig Clone()
    {
        return (GeminiThinkingConfig)this.MemberwiseClone();
    }
}

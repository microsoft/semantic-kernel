// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Google;

/// <summary>
/// GeminiGroundingConfig class
/// </summary>
public class GeminiGroundingConfig
{
    /// <summary>The Grounding with Google Search feature in the Gemini API can be used to improve the accuracy and recency of responses from the model.</summary>
    /// <remarks>
    /// The model can decide when to use Google Search.
    /// This parameter is valid from Gemini 2.0+.
    /// Combining Search with function calling is not yet supported. Functions will be ignored when this parameter is set.
    /// </remarks>
    [JsonPropertyName("google_search")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public object? GoogleSearch { get; set; }

    /// <summary>
    /// Clones this instance.
    /// </summary>
    /// <returns></returns>
    public GeminiGroundingConfig Clone()
    {
        return (GeminiGroundingConfig)this.MemberwiseClone();
    }
}

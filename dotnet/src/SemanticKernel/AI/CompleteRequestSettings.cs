// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.AI;

/// <summary>
/// Settings for a completion request.
/// </summary>
public class CompleteRequestSettings
{
    /// <summary>
    /// Temperature controls the randomness of the completion. The higher the temperature, the more random the completion.
    /// </summary>
    public double Temperature { get; set; } = 0;

    /// <summary>
    /// TopP controls the diversity of the completion. The higher the TopP, the more diverse the completion.
    /// </summary>
    public double TopP { get; set; } = 0;

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens based on whether they appear in the text so far, increasing the model's likelihood to talk about new topics.
    /// </summary>
    public double PresencePenalty { get; set; } = 0;

    /// <summary>
    /// Number between -2.0 and 2.0. Positive values penalize new tokens based on their existing frequency in the text so far, decreasing the model's likelihood to repeat the same line verbatim.
    /// </summary>
    public double FrequencyPenalty { get; set; } = 0;

    /// <summary>
    /// The maximum number of tokens to generate in the completion.
    /// </summary>
    public int MaxTokens { get; set; } = 100;

    /// <summary>
    /// Sequences where the completion will stop generating further tokens.
    /// </summary>
    public IList<string> StopSequences { get; set; } = Array.Empty<string>();
}

// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AI.MultiConnector;

public enum MaxTokensAdjustment
{
    /// <summary>
    ///No adjustment
    ///</summary>
    None,

    /// <summary>
    /// Adjust the max tokens to the minimum of the connector max tokens and the remaining tokens
    /// </summary>
    Percentage,

    /// <summary>
    /// Adjust the max tokens to the maximum of the connector max tokens and the remaining tokens
    /// </summary>
    CountInputTokens
}

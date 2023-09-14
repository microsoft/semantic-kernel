// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.TextCompletion;

/// <summary>
/// Request settings for an OpenAI text completion request.
/// </summary>
public class OpenAITextRequestSettings : OpenAIRequestSettings
{
    /// <summary>
    /// Construct a <see cref="OpenAITextRequestSettings"/> and set the default max tokens.
    /// </summary>
    public OpenAITextRequestSettings()
    {
        this.MaxTokens = 256;
    }
}

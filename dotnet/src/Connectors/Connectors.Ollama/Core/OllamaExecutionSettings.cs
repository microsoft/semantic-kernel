// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Ollama.Core;

/// <summary>
/// Ollama Execution Settings.
/// </summary>
public sealed class OllamaExecutionSettings
{
    /// <summary>
    /// Gets the specialization for the Ollama execution settings.
    /// </summary>
    /// <param name="promptExecutionSettings">Generic prompt execution settings.</param>
    /// <returns>Specialized Ollama execution settings.</returns>
    public static OllamaExecutionSettings FromExecutionSettings(PromptExecutionSettings? promptExecutionSettings)
    {
        throw new NotImplementedException();
    }

    /// <summary>
    /// Maximum number of tokens to generate.
    /// </summary>
    public int? MaxTokens { get; set; }
}

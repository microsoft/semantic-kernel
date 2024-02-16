// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Defines the purpose associated with the uploaded file.
/// </summary>
[Experimental("SKEXP0015")]
public enum OpenAIFilePurpose
{
    /// <summary>
    /// File to be used by assistants for model processing.
    /// </summary>
    Assistants,

    /// <summary>
    /// File to be used by fine-tuning jobs.
    /// </summary>
    FineTune,
}

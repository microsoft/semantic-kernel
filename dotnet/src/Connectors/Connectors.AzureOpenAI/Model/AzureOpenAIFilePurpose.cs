// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Defines the purpose associated with a file.
/// </summary>
[Experimental("SKEXP0010")]
public enum AzureOpenAIFilePurpose
{
    /// <summary>
    /// File to be used by assistants for model processing.
    /// </summary>
    Assistants,

    /// <summary>
    /// File to be used by assistants for model processing.
    /// </summary>
    AssistantsOutput,

    /// <summary>
    /// Files uploaded as a batch of API requests
    /// </summary>
    Batch,

    /// <summary>
    /// File produced as result of a file included as a batch request.
    /// </summary>
    BatchOutput,

    /// <summary>
    /// File to be used by fine-tuning jobs.
    /// </summary>
    FineTune,

    /// <summary>
    /// File produced as result of fine-tuning a model.
    /// </summary>
    FineTuneResults,

    /// <summary>
    /// File used for assistants image file inputs.
    /// </summary>
    Vision
}

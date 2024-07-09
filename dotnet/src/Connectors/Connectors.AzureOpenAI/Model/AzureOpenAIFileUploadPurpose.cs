// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Defines the purpose associated with the uploaded file.
/// </summary>
[Experimental("SKEXP0010")]
public enum AzureOpenAIFileUploadPurpose
{
    /// <summary>
    /// File to be used by assistants as input.
    /// </summary>
    Assistants,

    /// <summary>
    /// File to be used as input to fine-tune a model.
    /// </summary>
    FineTune,

    /// <summary>
    /// Files uploaded as a batch of API requests
    /// </summary>
    Batch,

    /// <summary>
    /// File to be used for assistants image file inputs.
    /// </summary>
    Vision
}

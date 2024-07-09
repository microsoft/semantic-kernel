// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// Execution settings associated with Azure Open AI file upload <see cref="AzureOpenAIFileService.UploadContentAsync"/>.
/// </summary>
[Experimental("SKEXP0010")]
public sealed class AzureOpenAIFileUploadExecutionSettings
{
    /// <summary>
    /// Initializes a new instance of the <see cref="AzureOpenAIFileUploadExecutionSettings"/> class.
    /// </summary>
    /// <param name="fileName">The file name</param>
    /// <param name="purpose">The file purpose</param>
    public AzureOpenAIFileUploadExecutionSettings(string fileName, AzureOpenAIFileUploadPurpose purpose)
    {
        Verify.NotNull(fileName, nameof(fileName));

        this.FileName = fileName;
        this.Purpose = purpose;
    }

    /// <summary>
    /// The file name.
    /// </summary>
    public string FileName { get; }

    /// <summary>
    /// The file purpose.
    /// </summary>
    public AzureOpenAIFileUploadPurpose Purpose { get; }
}

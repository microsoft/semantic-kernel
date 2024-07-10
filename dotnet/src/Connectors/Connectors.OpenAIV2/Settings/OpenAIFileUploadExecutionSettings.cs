// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using OpenAI.Files;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Execution settings associated with Open AI file upload <see cref="OpenAIFileService.UploadContentAsync"/>.
/// </summary>
[Experimental("SKEXP0010")]
public sealed class OpenAIFileUploadExecutionSettings
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIFileUploadExecutionSettings"/> class.
    /// </summary>
    /// <param name="fileName">The file name</param>
    /// <param name="purpose">The file purpose</param>
    public OpenAIFileUploadExecutionSettings(string fileName, FileUploadPurpose purpose)
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
    public FileUploadPurpose Purpose { get; }
}

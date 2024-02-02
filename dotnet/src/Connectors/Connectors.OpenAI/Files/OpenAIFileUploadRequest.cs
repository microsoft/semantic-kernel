// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// $$$
/// </summary>
public sealed class OpenAIFileUploadRequest
{
    /// <summary>
    /// Initializes a new instance of the <see cref="OpenAIFileUploadRequest"/> class.
    /// </summary>
    /// <param name="content">The file content</param>
    /// <param name="fileName">The file name</param>
    /// <param name="purpose">The file purpose</param>
    public OpenAIFileUploadRequest(BinaryContent content, string fileName, OpenAIFilePurpose purpose)
    {
        Verify.NotNull(fileName, nameof(fileName));

        this.FileName = fileName;
        this.Purpose = purpose;
        this.Content = content;
    }

    /// <summary>
    /// The file purpose.
    /// </summary>
    public OpenAIFilePurpose Purpose { get; }

    /// <summary>
    /// The file purpose.
    /// </summary>
    public string FileName { get; }

    /// <summary>
    /// The file name.
    /// </summary>
    public BinaryContent Content { get; }
}

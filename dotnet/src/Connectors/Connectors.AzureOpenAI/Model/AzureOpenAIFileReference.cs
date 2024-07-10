// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using OpenAI.Files;

namespace Microsoft.SemanticKernel.Connectors.AzureOpenAI;

/// <summary>
/// References an uploaded file by id.
/// </summary>
[Experimental("SKEXP0010")]
public sealed class AzureOpenAIFileReference
{
    /// <summary>
    /// The file identifier.
    /// </summary>
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// The timestamp the file was uploaded.s
    /// </summary>
    public DateTime CreatedTimestamp { get; set; }

    /// <summary>
    /// The name of the file.s
    /// </summary>
    public string FileName { get; set; } = string.Empty;

    /// <summary>
    /// Describes the associated purpose of the file.
    /// </summary>
    public OpenAIFilePurpose Purpose { get; set; }

    /// <summary>
    /// The file size, in bytes.
    /// </summary>
    public int SizeInBytes { get; set; }
}

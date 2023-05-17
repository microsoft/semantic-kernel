// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel.DataAnnotations;
using SemanticKernel.Service.Config;

namespace SemanticKernel.Service.CopilotChat.Config;

/// <summary>
/// File system storage configuration.
/// </summary>
public class FileSystemOptions
{
    /// <summary>
    /// Gets or sets the file path for persistent file system storage.
    /// </summary>
    [Required, NotEmptyOrWhitespace]
    public string FilePath { get; set; } = string.Empty;
}

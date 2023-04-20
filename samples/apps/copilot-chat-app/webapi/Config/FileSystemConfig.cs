// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Service.Config;

/// <summary>
/// File system storage configuration.
/// </summary>
public class FileSystemConfig
{
    /// <summary>
    /// Gets or sets the file path for persistent file system storage.
    /// </summary>
    public string FilePath { get; set; } = string.Empty;
}

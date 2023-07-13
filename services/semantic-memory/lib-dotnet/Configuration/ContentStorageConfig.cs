// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Services.Storage.ContentStorage;

namespace Microsoft.SemanticKernel.Services.Configuration;

public class ContentStorageConfig
{
    public string Type { get; set; } = "filesystem";
    public FileSystemConfig FileSystem { get; set; } = new();
    public AzureBlobConfig AzureBlobs { get; set; } = new();
}

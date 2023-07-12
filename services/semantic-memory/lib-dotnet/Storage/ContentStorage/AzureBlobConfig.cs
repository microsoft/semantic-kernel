// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Services.Storage.ContentStorage;

public class AzureBlobConfig
{
    public string Auth { get; set; } = "";
    public string Account { get; set; } = "";
    public string EndpointSuffix { get; set; } = "core.windows.net";
    public string ConnectionString { get; set; } = "";
    public string Container { get; set; } = "";
}

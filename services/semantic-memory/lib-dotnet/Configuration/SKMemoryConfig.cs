// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Services.Configuration;

public class SKMemoryConfig
{
    public ContentStorageConfig ContentStorage { get; set; } = new();
    public OrchestrationConfig Orchestration { get; set; } = new();
    public bool OpenApiEnabled { get; set; } = false;
}

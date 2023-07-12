// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Services.Storage.Pipeline;

namespace Microsoft.SemanticKernel.Services.Configuration;

public class OrchestrationConfig
{
    public string Type { get; set; } = "InProcess";
    public DistributedPipelineConfig DistributedPipeline { get; set; } = new();
}

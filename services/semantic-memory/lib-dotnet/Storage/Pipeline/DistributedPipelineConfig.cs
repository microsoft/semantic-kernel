// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Services.Storage.Queue;

namespace Microsoft.SemanticKernel.Services.Storage.Pipeline;

public class DistributedPipelineConfig
{
    public string Type { get; set; } = "rabbitmq";
    public AzureQueueConfig AzureQueue { get; set; } = new();
    public RabbitMqConfig RabbitMq { get; set; } = new();
    public FileBasedQueueConfig FileBasedQueue { get; set; } = new();
}

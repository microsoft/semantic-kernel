// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.Process.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class AzureOpenAIConfiguration(string serviceId, string deploymentName, string endpoint, string? apiKey = null, string? chatDeploymentName = null, string? modelId = null, string? chatModelId = null, string? embeddingModelId = null)
{
    public string ServiceId { get; set; } = serviceId;

    public string DeploymentName { get; set; } = deploymentName;

    public string ModelId { get; set; } = modelId ?? deploymentName;

    public string? ChatDeploymentName { get; set; } = chatDeploymentName ?? deploymentName;

    public string ChatModelId { get; set; } = chatModelId ?? deploymentName;

    public string EmbeddingModelId { get; set; } = embeddingModelId ?? "text-embedding-ada-002";

    public string Endpoint { get; set; } = endpoint;

    public string? ApiKey { get; set; } = apiKey;
}

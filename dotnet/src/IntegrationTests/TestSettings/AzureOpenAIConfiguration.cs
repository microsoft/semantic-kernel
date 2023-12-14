// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class AzureOpenAIConfiguration
{
    public string ServiceId { get; set; }

    public string DeploymentName { get; set; }

    public string EmbeddingModelId { get; set; }

    public string Endpoint { get; set; }

    public string ApiKey { get; set; }

    public AzureOpenAIConfiguration(string serviceId, string endpoint, string apiKey, string deploymentName, string? embeddingModelId = null)
    {
        this.ServiceId = serviceId;
        this.DeploymentName = deploymentName;
        this.EmbeddingModelId = embeddingModelId ?? "text-embedding-ada-002";
        this.Endpoint = endpoint;
        this.ApiKey = apiKey;
    }
}

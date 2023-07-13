// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class AzureOpenAIConfiguration
{
    public string ServiceId { get; set; }

    public string DeploymentName { get; set; }

    public string? ChatDeploymentName { get; set; }

    public string Endpoint { get; set; }

    public string ApiKey { get; set; }

    public AzureOpenAIConfiguration(string serviceId, string deploymentName, string endpoint, string apiKey, string? chatDeploymentName = null)
    {
        this.ServiceId = serviceId;
        this.DeploymentName = deploymentName;
        this.ChatDeploymentName = chatDeploymentName;
        this.Endpoint = endpoint;
        this.ApiKey = apiKey;
    }
}

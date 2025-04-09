// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.Experimental.Orchestration.Flow.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class AzureOpenAIConfiguration(string serviceId, string deploymentName, string endpoint, string apiKey, string? chatDeploymentName = null)
{
    public string ServiceId { get; set; } = serviceId;

    public string DeploymentName { get; set; } = deploymentName;

    public string? ChatDeploymentName { get; set; } = chatDeploymentName;

    public string Endpoint { get; set; } = endpoint;

    public string ApiKey { get; set; } = apiKey;
}

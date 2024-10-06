// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.Experimental.Orchestration.Flow.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
<<<<<<< Updated upstream
internal sealed class AzureOpenAIConfiguration(string serviceId, string deploymentName, string endpoint, string apiKey, string? chatDeploymentName = null)
=======
<<<<<<< main
internal sealed class AzureOpenAIConfiguration(string serviceId, string deploymentName, string endpoint, string apiKey, string? chatDeploymentName = null)
=======
<<<<<<< HEAD
internal sealed class AzureOpenAIConfiguration(string serviceId, string deploymentName, string endpoint, string apiKey, string? chatDeploymentName = null)
{
    public string ServiceId { get; set; } = serviceId;

    public string DeploymentName { get; set; } = deploymentName;

    public string? ChatDeploymentName { get; set; } = chatDeploymentName;

    public string Endpoint { get; set; } = endpoint;

    public string ApiKey { get; set; } = apiKey;
=======
internal sealed class AzureOpenAIConfiguration
>>>>>>> origin/main
>>>>>>> Stashed changes
{
    public string ServiceId { get; set; } = serviceId;

    public string DeploymentName { get; set; } = deploymentName;

    public string? ChatDeploymentName { get; set; } = chatDeploymentName;

    public string Endpoint { get; set; } = endpoint;

<<<<<<< Updated upstream
    public string ApiKey { get; set; } = apiKey;
=======
<<<<<<< main
    public string ApiKey { get; set; } = apiKey;
=======
    public string ApiKey { get; set; }

    public AzureOpenAIConfiguration(string serviceId, string deploymentName, string endpoint, string apiKey, string? chatDeploymentName = null)
    {
        this.ServiceId = serviceId;
        this.DeploymentName = deploymentName;
        this.ChatDeploymentName = chatDeploymentName;
        this.Endpoint = endpoint;
        this.ApiKey = apiKey;
    }
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> origin/main
>>>>>>> Stashed changes
}

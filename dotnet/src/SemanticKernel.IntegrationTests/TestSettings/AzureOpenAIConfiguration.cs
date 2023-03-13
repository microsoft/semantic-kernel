// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace SemanticKernel.IntegrationTests.TestSettings;

[SuppressMessage("Performance", "CA1812:Internal class that is apparently never instantiated",
    Justification = "Configuration classes are instantiated through IConfiguration.")]
internal sealed class AzureOpenAIConfiguration
{
    public string Label { get; set; }

    public string DeploymentName { get; set; }

    public string Endpoint { get; set; }

    public string ApiKey { get; set; }

    public AzureOpenAIConfiguration(string label, string deploymentName, string endpoint, string apiKey)
    {
        this.Label = label;
        this.DeploymentName = deploymentName;
        this.Endpoint = endpoint;
        this.ApiKey = apiKey;
    }
}

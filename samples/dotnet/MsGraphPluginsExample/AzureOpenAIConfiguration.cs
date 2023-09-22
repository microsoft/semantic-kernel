// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace MsGraphPluginsExample;

[SuppressMessage("Performance", "CA1812:class never instantiated", Justification = "Instantiated through IConfiguration")]
internal sealed class AzureOpenAIConfiguration
{
    public string ServiceId { get; set; }

    public string DeploymentName { get; set; }

    public string Endpoint { get; set; }

    public string ApiKey { get; set; }

    public AzureOpenAIConfiguration(string serviceId, string deploymentName, string endpoint, string apiKey)
    {
        this.ServiceId = serviceId;
        this.DeploymentName = deploymentName;
        this.Endpoint = endpoint;
        this.ApiKey = apiKey;
    }
}

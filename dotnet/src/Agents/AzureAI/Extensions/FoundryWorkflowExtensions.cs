// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure.AI.Agents.Persistent;
using Azure.Core;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Extensions for configuring the PersistentAgentsAdministrationClientOptions with a routing policy for Foundry Workflows.
/// </summary>
public static class FoundryWorkflowExtensions
{
    /// <summary>
    /// Adds a routing policy to the PersistentAgentsAdministrationClientOptions for Foundry Workflows.
    /// </summary>
    /// <param name="options"></param>
    /// <param name="endpoint"></param>
    /// <param name="apiVersion"></param>
    /// <returns></returns>
    /// <exception cref="ArgumentException"></exception>
    public static PersistentAgentsAdministrationClientOptions WithPolicy(this PersistentAgentsAdministrationClientOptions options, string endpoint, string apiVersion)
    {
        if (!Uri.TryCreate(endpoint, UriKind.Absolute, out var _endpoint))
        {
            throw new ArgumentException("The endpoint must be an absolute URI.", nameof(endpoint));
        }

        options.AddPolicy(new HttpPipelineRoutingPolicy(_endpoint, apiVersion), HttpPipelinePosition.PerCall);

        return options;
    }
}

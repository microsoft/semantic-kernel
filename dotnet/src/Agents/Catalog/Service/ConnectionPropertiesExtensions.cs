// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure.AI.Projects;

namespace Microsoft.SemanticKernel.Agents.Service;

/// <summary>
/// Extensions methods for the <see cref="ConnectionProperties"/>.
/// </summary>
public static class ConnectionPropertiesExtensions
{
    /// <summary>
    /// Retrieve the connection target or endpoint.
    /// </summary>
    /// <param name="connectionProperties">The target connection.</param>
    public static string GetEndpoint(this ConnectionProperties connectionProperties)
    {
        if (string.IsNullOrWhiteSpace(connectionProperties.Target))
        {
            throw new InvalidOperationException("The connection endpoint is missing or invalid.");
        }

        if (!Uri.TryCreate(connectionProperties.Target, UriKind.Absolute, out Uri? endpoint))
        {
            throw new InvalidOperationException("Invalid connection endpoint format.");
        }

        return connectionProperties.Target;
    }

    /// <summary>
    /// Retrieve the connection api key, if present.
    /// </summary>
    /// <param name="connectionProperties">The target connection.</param>
    public static string? GetApiKey(this ConnectionProperties connectionProperties)
    {
        if (connectionProperties.AuthType == AuthenticationType.ApiKey &&
            connectionProperties is ConnectionPropertiesApiKeyAuth apiKeyAuthProperties)
        {
            return apiKeyAuthProperties.Credentials.Key;
        }

        return null;
    }
}

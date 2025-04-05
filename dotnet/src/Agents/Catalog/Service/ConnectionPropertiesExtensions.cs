// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure.AI.Projects;

namespace Microsoft.SemanticKernel.Agents.Service;

/// <summary>
/// %%% COMMENT
/// </summary>
public static class ConnectionPropertiesExtensions
{
    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="connectionProperties"></param>
    /// <returns></returns>
    public static string GetEndpoint(this ConnectionProperties connectionProperties)
    {
        if (string.IsNullOrWhiteSpace(connectionProperties.Target))
        {
            throw new ArgumentException("The API key authentication target URI is missing or invalid."); // %%% EXCEPTION TYPE
        }

        if (!Uri.TryCreate(connectionProperties.Target, UriKind.Absolute, out Uri? endpoint))
        {
            throw new UriFormatException("Invalid URI format in API key authentication target."); // %%% EXCEPTION TYPE
        }

        return connectionProperties.Target;
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="connectionProperties"></param>
    /// <returns></returns>
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

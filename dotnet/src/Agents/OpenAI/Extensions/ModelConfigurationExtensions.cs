// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Provides extension methods for <see cref="ModelConfiguration"/>.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class ModelConfigurationExtensions
{
    /// <summary>
    /// Gets the endpoint property as a <see cref="Uri"/> from the specified <see cref="ModelConfiguration"/>.
    /// </summary>
    /// <param name="configuration">Model configuration</param>
    internal static Uri GetEndpointUri(this ModelConfiguration configuration)
    {
        Verify.NotNull(configuration);

        if (!configuration.ExtensionData.TryGetValue("endpoint", out var endpoint) || endpoint is null)
        {
            throw new InvalidOperationException("Endpoint was not specified.");
        }
        return new Uri(endpoint.ToString()!);
    }

    /// <summary>
    /// Gets the API key property as an <see cref="ApiKeyCredential"/> from the specified <see cref="ModelConfiguration"/>.
    /// </summary>
    /// <param name="configuration">Model configuration</param>
    internal static ApiKeyCredential GetApiKeyCredential(this ModelConfiguration configuration)
    {
        Verify.NotNull(configuration);

        if (!configuration.ExtensionData.TryGetValue("api_key", out var apiKey) || apiKey is null)
        {
            throw new InvalidOperationException("API key was not specified.");
        }

        return new ApiKeyCredential(apiKey.ToString()!);
    }
}

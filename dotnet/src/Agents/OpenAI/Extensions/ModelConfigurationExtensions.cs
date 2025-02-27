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
    internal static Uri? GetEndpointUri(this ModelConfiguration configuration)
    {
        Verify.NotNull(configuration);

        return configuration.ExtensionData.TryGetValue("endpoint", out var value) && value is not null && value is string endpoint
            ? new Uri(endpoint)
            : null;
    }

    /// <summary>
    /// Gets the API key property as an <see cref="ApiKeyCredential"/> from the specified <see cref="ModelConfiguration"/>.
    /// </summary>
    /// <param name="configuration">Model configuration</param>
    internal static ApiKeyCredential GetApiKeyCredential(this ModelConfiguration configuration)
    {
        Verify.NotNull(configuration);

        return !configuration.ExtensionData.TryGetValue("api_key", out var apiKey) || apiKey is null
            ? throw new InvalidOperationException("API key was not specified.")
            : new ApiKeyCredential(apiKey.ToString()!);
    }
}

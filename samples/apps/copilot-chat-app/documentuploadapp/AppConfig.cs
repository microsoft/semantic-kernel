// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;

namespace SemanticKernel.Service.DocumentUploadApp;

/// <summary>
/// Service configuration for the app.
/// </summary>
public sealed class ServiceConfig
{
    /// <summary>
    /// Client ID for the app as registered in Azure AD.
    /// </summary>
    public string ClientId { get; set; } = string.Empty;

    /// <summary>
    /// Redirect URI for the app as registered in Azure AD.
    /// </summary>
#pragma warning disable CA1056 // URI-like properties should not be strings
    public string RedirectUri { get; set; } = string.Empty;
#pragma warning restore CA1056 // URI-like properties should not be strings

    /// <summary>
    /// Uri for the service that is running the chat.
    /// </summary>
#pragma warning disable CA1056 // URI-like properties should not be strings
    public string ServiceUri { get; set; } = string.Empty;
#pragma warning restore CA1056 // URI-like properties should not be strings

    /// <summary>
    /// Gets service configuration from appsettings.json.
    /// </summary>
    /// <returns>An ServiceConfig instance</returns>
    public static ServiceConfig? GetServiceConfig()
    {
        var config = new ConfigurationBuilder()
            .AddJsonFile("appsettings.json")
            .Build();

        return config.GetRequiredSection("ServiceConfig").Get<ServiceConfig>();
    }

    /// <summary>
    /// Validates an ServiceConfig object.
    /// </summary>
    /// <param name="serviceConfig"></param>
    /// <returns>True is the config object is not null.</returns>
    public static bool Validate(ServiceConfig? serviceConfig)
    {
        return serviceConfig != null;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;

namespace ImportDocument;

/// <summary>
/// Configuration for the app.
/// </summary>
public sealed class Config
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
    /// Gets configuration from appsettings.json.
    /// </summary>
    /// <returns>An Config instance</returns>
    public static Config? GetConfig()
    {
        var config = new ConfigurationBuilder()
            .AddJsonFile("appsettings.json")
            .Build();

        return config.GetRequiredSection("Config").Get<Config>();
    }

    /// <summary>
    /// Validates a Config object.
    /// </summary>
    /// <param name="config"></param>
    /// <returns>True is the config object is not null.</returns>
    public static bool Validate(Config? config)
    {
        return config != null;
    }
}

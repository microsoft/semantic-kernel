// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;

namespace SemanticKernel.Service.DocumentUploadApp;

/// <summary>
/// Configuration for the app.
/// </summary>
public sealed class AppConfig
{
    /// <summary>
    /// Client ID for the app as registered in Azure AD.
    /// </summary>
    public string ClientId { get; set; } = string.Empty;

    /// <summary>
    /// Redirect URI for the app as registered in Azure AD.
    /// </summary>
    public string RedirectUri { get; set; } = string.Empty;

    /// <summary>
    /// Uri for the service that is running the chat.
    /// </summary>
    public string ServiceUri { get; set; } = string.Empty;

    /// <summary>
    /// Gets the app configuration from appsettings.json.
    /// </summary>
    /// <returns>An AppConfig instance</returns>
    public static AppConfig? GetAppConfig()
    {
        var config = new ConfigurationBuilder()
            .AddJsonFile("appsettings.json")
            .Build();

        return config.GetRequiredSection("AppConfig").Get<AppConfig>();
    }

    /// <summary>
    /// Validates an AppConfig object.
    /// </summary>
    /// <param name="appConfig"></param>
    /// <returns>True is the config object is not null.</returns>
    public static bool Validate(AppConfig? appConfig)
    {
        return appConfig != null;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using Azure.Core;
using Azure.Identity;
using Microsoft.Graph;

public static class GraphServiceProvider
{
    public static GraphServiceClient CreateGraphService()
    {
        string[] scopes;

        var config = new ConfigurationBuilder()
            .SetBasePath(Directory.GetCurrentDirectory()) // Set the base path for appsettings.json  
            .AddJsonFile("appsettings.json", optional: false, reloadOnChange: true) // Load appsettings.json  
            .AddUserSecrets<Program>()
            .AddEnvironmentVariables()
            .Build()
            .Get<AppConfig>() ??
            throw new InvalidOperationException("Configuration is not setup correctly.");

        config.Validate();

        TokenCredential credential = null!;
        if (config.AzureEntraId!.InteractiveBrowserAuthentication) // Authentication As User
        {
            /// Use this if using user delegated permissions
            scopes = ["User.Read", "Mail.Send"];

            credential = new InteractiveBrowserCredential(
                new InteractiveBrowserCredentialOptions
                {
                    TenantId = config.AzureEntraId.TenantId,
                    ClientId = config.AzureEntraId.ClientId,
                    AuthorityHost = AzureAuthorityHosts.AzurePublicCloud,
                    RedirectUri = new Uri(config.AzureEntraId.InteractiveBrowserRedirectUri!)
                });
        }
        else // Authentication As Application
        {
            scopes = ["https://graph.microsoft.com/.default"];

            credential = new ClientSecretCredential(
            config.AzureEntraId.TenantId,
            config.AzureEntraId.ClientId,
            config.AzureEntraId.ClientSecret);
        }

        return new GraphServiceClient(credential, scopes);
    }
}

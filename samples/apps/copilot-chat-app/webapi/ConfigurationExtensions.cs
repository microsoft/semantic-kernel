// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Reflection;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Hosting;

namespace SemanticKernel.Service;

internal static class ConfigExtensions
{
    /// <summary>
    /// Build the configuration for the service.
    /// </summary>
    public static IHostBuilder AddConfiguration(this IHostBuilder host)
    {
        string? environment = Environment.GetEnvironmentVariable("ASPNETCORE_ENVIRONMENT");

        host.ConfigureAppConfiguration((builderContext, configBuilder) =>
        {
            configBuilder.AddJsonFile(
                path: "appsettings.json",
                optional: false,
                reloadOnChange: true);

            configBuilder.AddJsonFile(
                path: $"appsettings.{environment}.json",
                optional: true,
                reloadOnChange: true);

            configBuilder.AddEnvironmentVariables();

            configBuilder.AddUserSecrets(
                assembly: Assembly.GetExecutingAssembly(),
                optional: true,
                reloadOnChange: true);

            // For settings from Key Vault, see https://learn.microsoft.com/en-us/aspnet/core/security/key-vault-configuration?view=aspnetcore-8.0
            string? keyVaultUri = builderContext.Configuration["Service:KeyVault"];
            if (!string.IsNullOrWhiteSpace(keyVaultUri))
            {
                configBuilder.AddAzureKeyVault(
                    new Uri(keyVaultUri),
                    new DefaultAzureCredential());

                // for more information on how to use DefaultAzureCredential, see https://learn.microsoft.com/en-us/dotnet/api/azure.identity.defaultazurecredential?view=azure-dotnet
            }
        });

        return host;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Microsoft.SemanticKernel.Functions.OpenAPI.Plugins;
using Microsoft.SemanticKernel.Orchestration;
using RepoUtils;

#pragma warning disable CA1861 // Avoid constant arrays as arguments
// ReSharper disable once InconsistentNaming
public static class Example22_OpenApiPlugin_AzureKeyVault
{
    private static readonly Uri s_pluginManifestUri = new("https://localhost:40443/.well-known/ai-plugin.json");
    private const string SecretName = "Foo";
    private const string SecretValue = "Bar";

    public static async Task RunAsync()
    {
        // To run this example, you must register a client application with the Microsoft identity platform.
        // Instructions here: https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app
        var authenticationProvider = new DynamicAuthenticationProvider(
            new Dictionary<string, Dictionary<string, string>>()
            {
                {
                    "login.microsoftonline.com",
                    new Dictionary<string, string>()
                    {
                        { "client_id", TestConfiguration.KeyVault.ClientId },
                        { "client_secret", TestConfiguration.KeyVault.ClientSecret },
                        { "grant_type", "client_credentials" }
                    }
                }
            },
            new Dictionary<string, string>()
        );

        await AddSecretToAzureKeyVaultAsync(authenticationProvider);
        await GetSecretFromAzureKeyVaultWithRetryAsync(authenticationProvider);
    }

    public static async Task GetSecretFromAzureKeyVaultWithRetryAsync(DynamicAuthenticationProvider authenticationProvider)
    {
        var kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithRetryBasic(new()
            {
                MaxRetryCount = 3,
                UseExponentialBackoff = true
            })
            .Build();

        // Import AI Plugin
        var plugin = await kernel.ImportPluginFunctionsAsync(
            PluginResourceNames.AzureKeyVault,
            s_pluginManifestUri,
            new OpenApiFunctionExecutionParameters { AuthCallback = authenticationProvider.AuthenticateRequestAsync });

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var contextVariables = new ContextVariables();
        contextVariables.Set("secret-name", SecretName);
        contextVariables.Set("server-url", TestConfiguration.KeyVault.Endpoint);
        contextVariables.Set("api-version", "7.0");

        // Run
        var kernelResult = await kernel.RunAsync(contextVariables, plugin["GetSecret"]);

        var result = kernelResult.GetValue<RestApiOperationResponse>();

        Console.WriteLine("GetSecret function result: {0}", result?.Content?.ToString());
    }

    public static async Task AddSecretToAzureKeyVaultAsync(DynamicAuthenticationProvider authenticationProvider)
    {
        var kernel = new KernelBuilder().WithLoggerFactory(ConsoleLogger.LoggerFactory).Build();

        // Import AI Plugin
        var plugin = await kernel.ImportPluginFunctionsAsync(
            PluginResourceNames.AzureKeyVault,
            s_pluginManifestUri,
            new OpenApiFunctionExecutionParameters
            {
                AuthCallback = authenticationProvider.AuthenticateRequestAsync,
                EnableDynamicPayload = true
            });

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var contextVariables = new ContextVariables();
        contextVariables.Set("secret-name", SecretName);
        contextVariables.Set("value", SecretValue);
        contextVariables.Set("server-url", TestConfiguration.KeyVault.Endpoint);
        contextVariables.Set("api-version", "7.0");
        contextVariables.Set("enabled", "true");

        // Run
        var kernelResult = await kernel.RunAsync(contextVariables, plugin["SetSecret"]);

        var result = kernelResult.GetValue<RestApiOperationResponse>();

        Console.WriteLine("SetSecret function result: {0}", result?.Content?.ToString());
    }
}

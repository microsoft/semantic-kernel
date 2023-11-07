// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Microsoft.SemanticKernel.Functions.OpenAPI.Plugins;
using Microsoft.SemanticKernel.Orchestration;
using RepoUtils;

#pragma warning disable CA1861 // Avoid constant arrays as arguments
// ReSharper disable once InconsistentNaming
public static class Example22_OpenApiPlugin_AzureKeyVault
{
    private const string ResourceName = $"{PluginResourceNames.AzureKeyVault}.ai-plugin.json";
    private const string SecretName = "Foo";
    private const string SecretValue = "Bar";

    /// <summary>
    /// This example demonstrates how to connect an Azure Key Vault plugin to the Semantic Kernel.
    /// To use this example, there are a few requirements:
    ///   1. Register a client application with the Microsoft identity platform.
    ///   https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app
    ///
    ///   2. Create an Azure Key Vault
    ///   https://learn.microsoft.com/en-us/azure/key-vault/general/quick-create-portal
    ///
    ///   3. Add a permission for Azure Key Vault to your client application
    ///   https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-configure-app-access-web-apis
    ///
    ///   4. Set your Key Vault endpoint, client ID, and client secret as user secrets using:
    ///   dotnet user-secrets set "KeyVault.Endpoint" "your_endpoint"
    ///   dotnet user-secrets set "KeyVault.ClientId" "your_client_id"
    ///   dotnet user-secrets set "KeyVault.ClientSecret" "your_secret"
    /// </summary>
    public static async Task RunAsync()
    {
        var authenticationProvider = new DynamicOpenAIAuthenticationProvider(
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

    public static async Task GetSecretFromAzureKeyVaultWithRetryAsync(DynamicOpenAIAuthenticationProvider authenticationProvider)
    {
        var kernel = new KernelBuilder()
            .WithLoggerFactory(ConsoleLogger.LoggerFactory)
            .WithRetryBasic(new()
            {
                MaxRetryCount = 3,
                UseExponentialBackoff = true
            })
            .Build();

        var type = typeof(PluginResourceNames);

        var stream = type.Assembly.GetManifestResourceStream(type, ResourceName);

        // Import an Open AI Plugin via Stream
        var plugin = await kernel.ImportOpenAIPluginFunctionsAsync(
            PluginResourceNames.AzureKeyVault,
            ResourceName,
            new OpenAIFunctionExecutionParameters { AuthCallback = authenticationProvider.AuthenticateRequestAsync });

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

    public static async Task AddSecretToAzureKeyVaultAsync(DynamicOpenAIAuthenticationProvider authenticationProvider)
    {
        var kernel = new KernelBuilder().WithLoggerFactory(ConsoleLogger.LoggerFactory).Build();

        // Import AI Plugin
        var plugin = await kernel.ImportOpenAIPluginFunctionsAsync(
            PluginResourceNames.AzureKeyVault,
            ResourceName,
            new OpenAIFunctionExecutionParameters
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

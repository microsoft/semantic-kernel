// Copyright (c) Microsoft. All rights reserved.

using System;
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
    public static async Task RunAsync()
    {
        // To run this example, you must register a client application with the Microsoft identity platform.
        // Instructions here: https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app
        var authenticationProvider = new InteractiveMsalAuthenticationProvider(
            TestConfiguration.KeyVault.ClientId,
            TestConfiguration.KeyVault.TenantId,
            new[] { "https://vault.azure.net/.default" },
            new Uri("http://localhost"));

        await GetSecretFromAzureKeyVaultWithRetryAsync(authenticationProvider);

        await AddSecretToAzureKeyVaultAsync(authenticationProvider);
    }

    public static async Task GetSecretFromAzureKeyVaultWithRetryAsync(InteractiveMsalAuthenticationProvider authenticationProvider)
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
        var resourceName = $"{PluginResourceNames.AzureKeyVault}.openapi.json";

        var stream = type.Assembly.GetManifestResourceStream(type, resourceName);

        // Import AI Plugin
        var plugin = await kernel.ImportPluginFunctionsAsync(
            PluginResourceNames.AzureKeyVault,
            stream!,
            new OpenApiFunctionExecutionParameters { AuthCallback = authenticationProvider.AuthenticateRequestAsync });

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var contextVariables = new ContextVariables();
        contextVariables.Set("server-url", TestConfiguration.KeyVault.Endpoint);
        contextVariables.Set("secret-name", "<secret-name>");
        contextVariables.Set("api-version", "7.0");

        // Run
        var kernelResult = await kernel.RunAsync(contextVariables, plugin["GetSecret"]);

        var result = kernelResult.GetValue<RestApiOperationResponse>();

        Console.WriteLine("GetSecret function result: {0}", result?.Content?.ToString());
    }

    public static async Task AddSecretToAzureKeyVaultAsync(InteractiveMsalAuthenticationProvider authenticationProvider)
    {
        var kernel = new KernelBuilder().WithLoggerFactory(ConsoleLogger.LoggerFactory).Build();

        var type = typeof(PluginResourceNames);
        var resourceName = $"{PluginResourceNames.AzureKeyVault}.openapi.json";

        var stream = type.Assembly.GetManifestResourceStream(type, resourceName);

        // Import AI Plugin
        var plugin = await kernel.ImportPluginFunctionsAsync(
            PluginResourceNames.AzureKeyVault,
            stream!,
            new OpenApiFunctionExecutionParameters
            {
                AuthCallback = authenticationProvider.AuthenticateRequestAsync,
                EnableDynamicPayload = true
            });

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var contextVariables = new ContextVariables();
        contextVariables.Set("server-url", TestConfiguration.KeyVault.Endpoint);
        contextVariables.Set("secret-name", "<secret-name>");
        contextVariables.Set("api-version", "7.0");
        contextVariables.Set("value", "<secret-value>");
        contextVariables.Set("enabled", "<enabled>");

        // Run
        var kernelResult = await kernel.RunAsync(contextVariables, plugin["SetSecret"]);

        var result = kernelResult.GetValue<RestApiOperationResponse>();

        Console.WriteLine("SetSecret function result: {0}", result?.Content?.ToString());
    }
}

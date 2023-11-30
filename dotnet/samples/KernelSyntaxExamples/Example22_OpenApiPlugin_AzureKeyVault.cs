// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Microsoft.SemanticKernel.Functions.OpenAPI.Plugins;
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
            .Build();

        var type = typeof(PluginResourceNames);
        var resourceName = $"{PluginResourceNames.AzureKeyVault}.openapi.json";

        var stream = type.Assembly.GetManifestResourceStream(type, resourceName);

        // Import an Open AI Plugin via Stream
        var plugin = await kernel.ImportPluginFromOpenApiAsync(
            PluginResourceNames.AzureKeyVault,
            stream!,
            new OpenApiFunctionExecutionParameters
            {
                AuthCallback = authenticationProvider.AuthenticateRequestAsync,
                ServerUrlOverride = new Uri(TestConfiguration.KeyVault.Endpoint),
            });

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var arguments = new KernelFunctionArguments();
        arguments["secret-name"] = "<secret-name>";
        arguments["api-version"] = "7.0";

        // Run
        var functionResult = await kernel.InvokeAsync(plugin["GetSecret"], arguments);

        var result = functionResult.GetValue<RestApiOperationResponse>();

        Console.WriteLine("GetSecret function result: {0}", result?.Content?.ToString());
    }

    public static async Task AddSecretToAzureKeyVaultAsync(InteractiveMsalAuthenticationProvider authenticationProvider)
    {
        var kernel = new KernelBuilder().WithLoggerFactory(ConsoleLogger.LoggerFactory).Build();

        var type = typeof(PluginResourceNames);
        var resourceName = $"{PluginResourceNames.AzureKeyVault}.openapi.json";

        var stream = type.Assembly.GetManifestResourceStream(type, resourceName);

        // Import AI Plugin
        var plugin = await kernel.ImportPluginFromOpenApiAsync(
            PluginResourceNames.AzureKeyVault,
            stream!,
            new OpenApiFunctionExecutionParameters
            {
                AuthCallback = authenticationProvider.AuthenticateRequestAsync,
                EnableDynamicPayload = true
            });

        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var arguments = new KernelFunctionArguments
        {
            ["server-url"] = TestConfiguration.KeyVault.Endpoint,
            ["secret-name"] = "<secret-name>",
            ["api-version"] = "7.0",
            ["value"] = "<secret-value>",
            ["enabled"] = "<enabled>",
        };

        // Run
        var functionResult = await kernel.InvokeAsync(plugin["SetSecret"], arguments);

        var result = functionResult.GetValue<RestApiOperationResponse>();

        Console.WriteLine("SetSecret function result: {0}", result?.Content?.ToString());
    }
}

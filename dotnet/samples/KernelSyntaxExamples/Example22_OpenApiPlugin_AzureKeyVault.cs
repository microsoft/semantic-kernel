// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Net.Mime;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;
using Microsoft.SemanticKernel.Functions.OpenAPI.OpenAI;
using Microsoft.SemanticKernel.Functions.OpenAPI.Plugins;
using Microsoft.SemanticKernel.Orchestration;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example22_OpenApiPlugin_AzureKeyVault
{
    private const string OpenAIManifestResourceName = $"{PluginResourceNames.AzureKeyVault}.ai-plugin.json";
    private const string OpenApiSpecResourceName = $"{PluginResourceNames.AzureKeyVault}.openapi.json";
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
    ///
    /// 5. Replace your tenant ID with the "TENANT_ID" placeholder in dotnet/src/Functions/Functions.OpenAPI/Plugins/AzureKeyVaultPlugin/ai-plugin.json
    /// </summary>
    public static async Task RunAsync()
    {
        var authenticationProvider = new OpenAIAuthenticationProvider(
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

        var kernel = new KernelBuilder().WithLoggerFactory(ConsoleLogger.LoggerFactory).Build();

        var type = typeof(PluginResourceNames);
        using StreamReader reader = new(type.Assembly.GetManifestResourceStream(type, OpenApiSpecResourceName)!);
        var content = await reader.ReadToEndAsync().ConfigureAwait(false);
        var messageStub = new HttpMessageHandlerStub(content);
        var httpClient = new HttpClient(messageStub);

        // Import Open AI Plugin
        var stream = type.Assembly.GetManifestResourceStream(type, OpenAIManifestResourceName);
        var plugin = await kernel.ImportOpenAIPluginFunctionsAsync(
            PluginResourceNames.AzureKeyVault,
            stream!,
            new OpenAIFunctionExecutionParameters
            {
                AuthCallback = authenticationProvider.AuthenticateRequestAsync,
                HttpClient = httpClient,
                EnableDynamicPayload = true
            });

        await AddSecretToAzureKeyVaultAsync(kernel, plugin);
        await GetSecretFromAzureKeyVaultWithRetryAsync(kernel, plugin);

        messageStub.Dispose();
        httpClient.Dispose();
    }

    public static async Task AddSecretToAzureKeyVaultAsync(IKernel kernel, IDictionary<string, ISKFunction> plugin)
    {
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

    public static async Task GetSecretFromAzureKeyVaultWithRetryAsync(IKernel kernel, IDictionary<string, ISKFunction> plugin)
    {
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
}

#region Utility Classes

internal sealed class HttpMessageHandlerStub : DelegatingHandler
{
    public HttpResponseMessage ResponseToReturn { get; set; }

    public HttpMessageHandlerStub(string responseToReturn)
    {
        this.ResponseToReturn = new HttpResponseMessage(System.Net.HttpStatusCode.OK)
        {
            Content = new StringContent(responseToReturn, Encoding.UTF8, MediaTypeNames.Application.Json)
        };
    }

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        if (request.RequestUri!.Scheme.Equals("file", StringComparison.OrdinalIgnoreCase))
        {
            return this.ResponseToReturn;
        }

        using var httpClient = new HttpClient();
        using var newRequest = new HttpRequestMessage() // construct a new request because the same one cannot be sent twice
        {
            Content = request.Content,
            Method = request.Method,
            RequestUri = request.RequestUri,
        };

        foreach (var header in request.Headers)
        {
            newRequest.Headers.Add(header.Key, header.Value);
        }
        return await httpClient.SendAsync(newRequest, cancellationToken).ConfigureAwait(false);
    }
}

#endregion

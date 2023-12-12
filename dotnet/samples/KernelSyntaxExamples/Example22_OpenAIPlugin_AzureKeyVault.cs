// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Net.Mime;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Resources;

// ReSharper disable once InconsistentNaming
public static class Example22_OpenAIPlugin_AzureKeyVault
{
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
    ///   dotnet user-secrets set "KeyVault:Endpoint" "your_endpoint"
    ///   dotnet user-secrets set "KeyVault:ClientId" "your_client_id"
    ///   dotnet user-secrets set "KeyVault:ClientSecret" "your_secret"
    ///
    ///   5. Replace your tenant ID with the "TENANT_ID" placeholder in dotnet/samples/KernelSyntaxExamples/Resources/22-ai-plugin.json
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
            }
        );

        Kernel kernel = new();

        var openApiSpec = EmbeddedResource.Read("22-openapi.json");
        using var messageStub = new HttpMessageHandlerStub(openApiSpec);
        using var httpClient = new HttpClient(messageStub);

        // Import Open AI Plugin
        var openAIManifest = EmbeddedResource.ReadStream("22-ai-plugin.json");
        var plugin = await kernel.ImportPluginFromOpenAIAsync(
            "AzureKeyVaultPlugin",
            openAIManifest!,
            new OpenAIFunctionExecutionParameters
            {
                AuthCallback = authenticationProvider.AuthenticateRequestAsync,
                HttpClient = httpClient,
                EnableDynamicPayload = true,
                ServerUrlOverride = new Uri(TestConfiguration.KeyVault.Endpoint)
            });

        await AddSecretToAzureKeyVaultAsync(kernel, plugin);
        await GetSecretFromAzureKeyVaultWithRetryAsync(kernel, plugin);
    }

    public static async Task AddSecretToAzureKeyVaultAsync(Kernel kernel, KernelPlugin plugin)
    {
        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var arguments = new KernelArguments
        {
            ["secret-name"] = SecretName,
            ["value"] = SecretValue,
            ["api-version"] = "7.0",
            ["enabled"] = "true",
        };

        // Run
        var functionResult = await kernel.InvokeAsync(plugin["SetSecret"], arguments);

        var result = functionResult.GetValue<RestApiOperationResponse>();

        Console.WriteLine("SetSecret function result: {0}", result?.Content?.ToString());
    }

    public static async Task GetSecretFromAzureKeyVaultWithRetryAsync(Kernel kernel, KernelPlugin plugin)
    {
        // Add arguments for required parameters, arguments for optional ones can be skipped.
        var arguments = new KernelArguments();
        arguments["secret-name"] = SecretName;
        arguments["api-version"] = "7.0";

        // Run
        var functionResult = await kernel.InvokeAsync(plugin["GetSecret"], arguments);

        var result = functionResult.GetValue<RestApiOperationResponse>();

        Console.WriteLine("GetSecret function result: {0}", result?.Content?.ToString());
    }
}

#region Utility Classes

/// <summary>
/// Provides authentication for HTTP requests to OpenAI using OAuth or verification tokens.
/// </summary>
internal sealed class OpenAIAuthenticationProvider
{
    private readonly Dictionary<string, Dictionary<string, string>> _oAuthValues;
    private readonly Dictionary<string, string> _credentials;

    /// <summary>
    /// Creates an instance of the <see cref="OpenAIAuthenticationProvider"/> class.
    /// </summary>
    /// <param name="oAuthValues">A dictionary containing OAuth values for each authentication scheme.</param>
    /// <param name="credentials">A dictionary containing credentials for each authentication scheme.</param>
    public OpenAIAuthenticationProvider(Dictionary<string, Dictionary<string, string>>? oAuthValues = null, Dictionary<string, string>? credentials = null)
    {
        this._oAuthValues = oAuthValues ?? new();
        this._credentials = credentials ?? new();
    }

    /// <summary>
    /// Applies the authentication content to the provided HTTP request message.
    /// </summary>
    /// <param name="request">The HTTP request message.</param>
    /// <param name="pluginName">Name of the plugin</param>
    /// <param name="openAIAuthConfig ">The <see cref="OpenAIAuthenticationConfig"/> used to authenticate.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    public async Task AuthenticateRequestAsync(HttpRequestMessage request, string pluginName, OpenAIAuthenticationConfig openAIAuthConfig, CancellationToken cancellationToken = default)
    {
        if (openAIAuthConfig.Type == OpenAIAuthenticationType.None)
        {
            return;
        }

        string scheme = "";
        string credential = "";

        if (openAIAuthConfig.Type == OpenAIAuthenticationType.OAuth)
        {
            var domainOAuthValues = this._oAuthValues[openAIAuthConfig.AuthorizationUrl!.Host]
                ?? throw new KernelException("No OAuth values found for the provided authorization URL.");

            var values = new Dictionary<string, string>(domainOAuthValues) {
                { "scope", openAIAuthConfig.Scope ?? "" },
            };

            using HttpContent? requestContent = openAIAuthConfig.AuthorizationContentType switch
            {
                "application/x-www-form-urlencoded" => new FormUrlEncodedContent(values),
                "application/json" => new StringContent(JsonSerializer.Serialize(values), Encoding.UTF8, "application/json"),
                _ => throw new KernelException($"Unsupported authorization content type: {openAIAuthConfig.AuthorizationContentType}"),
            };

            // Request the token
            using var client = new HttpClient();
            using var authRequest = new HttpRequestMessage(HttpMethod.Post, openAIAuthConfig.AuthorizationUrl) { Content = requestContent };
            var response = await client.SendAsync(authRequest, cancellationToken).ConfigureAwait(false);

            response.EnsureSuccessStatusCode();

            // Read the token
            var responseContent = await response.Content.ReadAsStringAsync(cancellationToken).ConfigureAwait(false);
            OAuthTokenResponse? tokenResponse;
            try
            {
                tokenResponse = JsonSerializer.Deserialize<OAuthTokenResponse>(responseContent);
            }
            catch (JsonException)
            {
                throw new KernelException($"Failed to deserialize token response from {openAIAuthConfig.AuthorizationUrl}.");
            }

            // Get the token type and value
            scheme = tokenResponse?.TokenType ?? throw new KernelException("No token type found in the response.");
            credential = tokenResponse?.AccessToken ?? throw new KernelException("No access token found in the response.");
        }
        else
        {
            var token = openAIAuthConfig.VerificationTokens?[pluginName]
                ?? throw new KernelException("No verification token found for the provided plugin name.");

            scheme = openAIAuthConfig.AuthorizationType.ToString();
            credential = token;
        }

        request.Headers.Authorization = new AuthenticationHeaderValue(scheme, credential);
    }
}

/// <summary>
/// Represents the authentication section for an OpenAI plugin.
/// </summary>
#pragma warning disable CA1812 // Avoid uninstantiated internal classes
internal sealed class OAuthTokenResponse
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
{
    /// <summary>
    /// The type of access token.
    /// </summary>
    [JsonPropertyName("token_type")]
    public string TokenType { get; set; } = "";

    /// <summary>
    /// The authorization scope.
    /// </summary>
    [JsonPropertyName("access_token")]
    public string AccessToken { get; set; } = "";
}

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

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Functions.OpenAPI.Authentication;
using Microsoft.SemanticKernel.Functions.OpenAPI.Extensions;
using Microsoft.SemanticKernel.Orchestration;

using Newtonsoft.Json;
using RepoUtils;

/// <summary>
/// This sample shows how to connect the Semantic Kernel to Jira as an Open Api plugin based on the Open Api schema.
/// This format of registering the plugin and its operations, and subsequently executing those operations can be applied
/// to an Open Api plugin that follows the Open Api Schema.
/// </summary>
// ReSharper disable once InconsistentNaming
public static class Example24_OpenApiPlugin_Jira
{
    public static async Task RunAsync()
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    {
        var kernel = new KernelBuilder().WithLoggerFactory(ConsoleLogger.LoggerFactory).Build();
        var contextVariables = new ContextVariables();
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    {
        var kernel = new KernelBuilder().WithLoggerFactory(ConsoleLogger.LoggerFactory).Build();
        var contextVariables = new ContextVariables();
=======
<<<<<<< div
=======
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
    {
        var kernel = new KernelBuilder().WithLoggerFactory(ConsoleLogger.LoggerFactory).Build();
        var contextVariables = new ContextVariables();

        // Change <your-domain> to a jira instance you have access to with your authentication credentials
        string serverUrl = $"https://{TestConfiguration.Jira.Domain}.atlassian.net/rest/api/latest/";
        contextVariables.Set("server-url", serverUrl);

        IDictionary<string, ISKFunction> jiraFunctions;
// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Identity.Client;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;
using Xunit.Abstractions;

namespace Examples;

public class Example24_OpenApiPlugin_Jira : BaseTest
{
    private static readonly JsonSerializerOptions s_jsonOptionsCache = new()
    {
        WriteIndented = true
    };

    /// <summary>
    /// This sample shows how to connect the Semantic Kernel to Jira as an Open API plugin based on the Open API schema.
    /// This format of registering the plugin and its operations, and subsequently executing those operations can be applied
    /// to an Open API plugin that follows the Open API Schema.
    /// To use this example, there are a few requirements:
    /// 1. You must have a Jira instance that you can authenticate to with your email and api key.
    ///    Follow the instructions here to get your api key:
    ///    https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/
    /// 2. You must create a new project in your Jira instance and create two issues named TEST-1 and TEST-2 respectively.
    ///    Follow the instructions here to create a new project and issues:
    ///    https://support.atlassian.com/jira-software-cloud/docs/create-a-new-project/
    ///    https://support.atlassian.com/jira-software-cloud/docs/create-an-issue-and-a-sub-task/
    /// 3. You can find your domain under the "Products" tab in your account management page.
    ///    To go to your account management page, click on your profile picture in the top right corner of your Jira
    ///    instance then select "Manage account".
    /// 4. Configure the secrets as described by the ReadMe.md in the dotnet/samples/KernelSyntaxExamples folder.
    /// </summary>
    [Fact(Skip = "Setup credentials")]
    public async Task RunAsync()
    {
        Kernel kernel = new();
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        // Change <your-domain> to a jira instance you have access to with your authentication credentials
        string serverUrl = $"https://{TestConfiguration.Jira.Domain}.atlassian.net/rest/api/latest/";
        contextVariables.Set("server-url", serverUrl);

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        IDictionary<string, ISKFunction> jiraFunctions;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        IDictionary<string, ISKFunction> jiraFunctions;
=======
        KernelPlugin jiraFunctions;
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        KernelPlugin jiraFunctions;
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
        KernelPlugin jiraFunctions;
>>>>>>> main
=======
>>>>>>> head
        var tokenProvider = new BasicAuthenticationProvider(() =>
        {
            string s = $"{TestConfiguration.Jira.Email}:{TestConfiguration.Jira.ApiKey}";
            return Task.FromResult(s);
        });

        using HttpClient httpClient = new();

        // The bool useLocalFile can be used to toggle the ingestion method for the openapi schema between a file path and a URL
        bool useLocalFile = true;
        if (useLocalFile)
        {
            var apiPluginFile = "./../../../Plugins/JiraPlugin/openapi.json";
            jiraFunctions = await kernel.ImportPluginFunctionsAsync("jiraPlugin", apiPluginFile, new OpenApiFunctionExecutionParameters(authCallbackProvider: (_) => tokenProvider.AuthenticateRequestAsync));
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head
            jiraFunctions = await kernel.ImportPluginFromOpenApiAsync(
                "jiraPlugin",
                apiPluginFile,
                new OpenApiFunctionExecutionParameters(
                    authCallback: tokenProvider.AuthenticateRequestAsync,
                    serverUrlOverride: new Uri(serverUrl)
                )
            );
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        }
        else
        {
            var apiPluginRawFileURL = new Uri("https://raw.githubusercontent.com/microsoft/PowerPlatformConnectors/dev/certified-connectors/JIRA/apiDefinition.swagger.json");
            jiraFunctions = await kernel.ImportPluginFunctionsAsync("jiraPlugin", apiPluginRawFileURL, new OpenApiFunctionExecutionParameters(authCallbackProvider: (_) => tokenProvider.AuthenticateRequestAsync));
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
>>>>>>> head
        }

        // GetIssue Function
        {
            // Set Properties for the Get Issue operation in the openAPI.swagger.json
            contextVariables.Set("issueKey", "SKTES-2");

            // Run operation via the semantic kernel
            var result = await kernel.RunAsync(contextVariables, jiraFunctions["GetIssue"]);

            Console.WriteLine("\n\n\n");
            var formattedContent = JsonConvert.SerializeObject(JsonConvert.DeserializeObject(result.GetValue<string>()!), Formatting.Indented);
            Console.WriteLine("GetIssue jiraPlugin response: \n{0}", formattedContent);
        }

        // AddComment Function
        {
            // Set Properties for the AddComment operation in the openAPI.swagger.json
            contextVariables.Set("issueKey", "SKTES-1");
            contextVariables.Set("body", "Here is a rad comment");

            // Run operation via the semantic kernel
            var result = await kernel.RunAsync(contextVariables, jiraFunctions["AddComment"]);

            Console.WriteLine("\n\n\n");
            var formattedContent = JsonConvert.SerializeObject(JsonConvert.DeserializeObject(result.GetValue<string>()!), Formatting.Indented);
            Console.WriteLine("AddComment jiraPlugin response: \n{0}", formattedContent);
        }
    }
            jiraFunctions = await kernel.ImportPluginFromOpenApiAsync(
                "jiraPlugin",
                apiPluginRawFileURL,
                new OpenApiFunctionExecutionParameters(
                    httpClient, tokenProvider.AuthenticateRequestAsync,
                    serverUrlOverride: new Uri(serverUrl)
                )
            );
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        }

        // GetIssue Function
        {
            // Set Properties for the Get Issue operation in the openAPI.swagger.json
            contextVariables.Set("issueKey", "SKTES-2");

            // Run operation via the semantic kernel
            var result = await kernel.RunAsync(contextVariables, jiraFunctions["GetIssue"]);

<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
            Console.WriteLine("\n\n\n");
            var formattedContent = JsonConvert.SerializeObject(JsonConvert.DeserializeObject(result.GetValue<string>()!), Formatting.Indented);
            Console.WriteLine("GetIssue jiraPlugin response: \n{0}", formattedContent);
        }
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> Stashed changes
>>>>>>> head
        WriteLine("\n\n\n");
        var formattedContent = JsonSerializer.Serialize(
            result.GetValue<RestApiOperationResponse>(), s_jsonOptionsCache);
        WriteLine($"GetIssue jiraPlugin response: \n{formattedContent}");
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head

        // AddComment Function
        {
            // Set Properties for the AddComment operation in the openAPI.swagger.json
            contextVariables.Set("issueKey", "SKTES-1");
            contextVariables.Set("body", "Here is a rad comment");

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
<<<<<<< main
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
            // Run operation via the semantic kernel
            var result = await kernel.RunAsync(contextVariables, jiraFunctions["AddComment"]);

<<<<<<< div
<<<<<<< div
=======
<<<<<<< head
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
            // Run operation via the semantic kernel
            var result = await kernel.RunAsync(contextVariables, jiraFunctions["AddComment"]);

<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
            Console.WriteLine("\n\n\n");
            var formattedContent = JsonConvert.SerializeObject(JsonConvert.DeserializeObject(result.GetValue<string>()!), Formatting.Indented);
            Console.WriteLine("AddComment jiraPlugin response: \n{0}", formattedContent);
        }
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
<<<<<<< div
>>>>>>> main
=======
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        WriteLine("\n\n\n");

        formattedContent = JsonSerializer.Serialize(result.GetValue<RestApiOperationResponse>(), s_jsonOptionsCache);
        WriteLine($"AddComment jiraPlugin response: \n{formattedContent}");
    }
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
>>>>>>> head

    #region Example of authentication providers

    /// <summary>
    /// Retrieves authentication content (e.g. username/password, API key) via the provided delegate and
    /// applies it to HTTP requests using the "basic" authentication scheme.
    /// </summary>
    public class BasicAuthenticationProvider
    {
        private readonly Func<Task<string>> _credentials;

        /// <summary>
        /// Creates an instance of the <see cref="BasicAuthenticationProvider"/> class.
        /// </summary>
        /// <param name="credentials">Delegate for retrieving credentials.</param>
        public BasicAuthenticationProvider(Func<Task<string>> credentials)
        {
            this._credentials = credentials;
        }

        /// <summary>
        /// Applies the authentication content to the provided HTTP request message.
        /// </summary>
        /// <param name="request">The HTTP request message.</param>
        /// <param name="cancellationToken">The cancellation token.</param>
        public async Task AuthenticateRequestAsync(HttpRequestMessage request, CancellationToken cancellationToken = default)
        {
            // Base64 encode
            string encodedContent = Convert.ToBase64String(Encoding.UTF8.GetBytes(await this._credentials().ConfigureAwait(false)));
            request.Headers.Authorization = new AuthenticationHeaderValue("Basic", encodedContent);
        }
    }

    /// <summary>
    /// Retrieves a token via the provided delegate and applies it to HTTP requests using the
    /// "bearer" authentication scheme.
    /// </summary>
    public class BearerAuthenticationProvider
    {
        private readonly Func<Task<string>> _bearerToken;

<<<<<<< div
=======
=======
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
>>>>>>> head

    #region Example of authentication providers

    /// <summary>
    /// Retrieves authentication content (e.g. username/password, API key) via the provided delegate and
    /// applies it to HTTP requests using the "basic" authentication scheme.
    /// </summary>
    public class BasicAuthenticationProvider
    {
        private readonly Func<Task<string>> _credentials;

        /// <summary>
        /// Creates an instance of the <see cref="BasicAuthenticationProvider"/> class.
        /// </summary>
        /// <param name="credentials">Delegate for retrieving credentials.</param>
        public BasicAuthenticationProvider(Func<Task<string>> credentials)
        {
            this._credentials = credentials;
        }

        /// <summary>
        /// Applies the authentication content to the provided HTTP request message.
        /// </summary>
        /// <param name="request">The HTTP request message.</param>
        /// <param name="cancellationToken">The cancellation token.</param>
        public async Task AuthenticateRequestAsync(HttpRequestMessage request, CancellationToken cancellationToken = default)
        {
            // Base64 encode
            string encodedContent = Convert.ToBase64String(Encoding.UTF8.GetBytes(await this._credentials().ConfigureAwait(false)));
            request.Headers.Authorization = new AuthenticationHeaderValue("Basic", encodedContent);
        }
    }

    /// <summary>
    /// Retrieves a token via the provided delegate and applies it to HTTP requests using the
    /// "bearer" authentication scheme.
    /// </summary>
    public class BearerAuthenticationProvider
    {
        private readonly Func<Task<string>> _bearerToken;

<<<<<<< div
>>>>>>> main
=======
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
        /// <summary>
        /// Creates an instance of the <see cref="BearerAuthenticationProvider"/> class.
        /// </summary>
        /// <param name="bearerToken">Delegate to retrieve the bearer token.</param>
        public BearerAuthenticationProvider(Func<Task<string>> bearerToken)
        {
            this._bearerToken = bearerToken;
        }

        /// <summary>
        /// Applies the token to the provided HTTP request message.
        /// </summary>
        /// <param name="request">The HTTP request message.</param>
        public async Task AuthenticateRequestAsync(HttpRequestMessage request)
        {
            var token = await this._bearerToken().ConfigureAwait(false);
            request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        }
    }

    /// <summary>
    /// Uses the Microsoft Authentication Library (MSAL) to authenticate HTTP requests.
    /// </summary>
    public class InteractiveMsalAuthenticationProvider : BearerAuthenticationProvider
    {
        /// <summary>
        /// Creates an instance of the <see cref="InteractiveMsalAuthenticationProvider"/> class.
        /// </summary>
        /// <param name="clientId">Client ID of the caller.</param>
        /// <param name="tenantId">Tenant ID of the target resource.</param>
        /// <param name="scopes">Requested scopes.</param>
        /// <param name="redirectUri">Redirect URI.</param>
        public InteractiveMsalAuthenticationProvider(string clientId, string tenantId, string[] scopes, Uri redirectUri)
            : base(() => GetTokenAsync(clientId, tenantId, scopes, redirectUri))
        {
        }

        /// <summary>
        /// Gets an access token using the Microsoft Authentication Library (MSAL).
        /// </summary>
        /// <param name="clientId">Client ID of the caller.</param>
        /// <param name="tenantId">Tenant ID of the target resource.</param>
        /// <param name="scopes">Requested scopes.</param>
        /// <param name="redirectUri">Redirect URI.</param>
        /// <returns>Access token.</returns>
        private static async Task<string> GetTokenAsync(string clientId, string tenantId, string[] scopes, Uri redirectUri)
        {
            IPublicClientApplication app = PublicClientApplicationBuilder.Create(clientId)
                .WithRedirectUri(redirectUri.ToString())
                .WithTenantId(tenantId)
                .Build();

            IEnumerable<IAccount> accounts = await app.GetAccountsAsync().ConfigureAwait(false);
            AuthenticationResult result;
            try
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
            {
                result = await app.AcquireTokenSilent(scopes, accounts.FirstOrDefault())
                    .ExecuteAsync().ConfigureAwait(false);
            }
            catch (MsalUiRequiredException)
            {
=======
<<<<<<< div
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
            {
                result = await app.AcquireTokenSilent(scopes, accounts.FirstOrDefault())
                    .ExecuteAsync().ConfigureAwait(false);
            }
            catch (MsalUiRequiredException)
            {
<<<<<<< div
>>>>>>> main
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
                // A MsalUiRequiredException happened on AcquireTokenSilent.
                // This indicates you need to call AcquireTokenInteractive to acquire a token
                result = await app.AcquireTokenInteractive(scopes)
                    .ExecuteAsync().ConfigureAwait(false);
            }

            return result.AccessToken;
        }
    }

    /// <summary>
    /// Retrieves authentication content (scheme and value) via the provided delegate and applies it to HTTP requests.
    /// </summary>
    public sealed class CustomAuthenticationProvider
    {
        private readonly Func<Task<string>> _header;
        private readonly Func<Task<string>> _value;

        /// <summary>
        /// Creates an instance of the <see cref="CustomAuthenticationProvider"/> class.
        /// </summary>
        /// <param name="header">Delegate for retrieving the header name.</param>
        /// <param name="value">Delegate for retrieving the value.</param>
        public CustomAuthenticationProvider(Func<Task<string>> header, Func<Task<string>> value)
        {
            this._header = header;
            this._value = value;
        }

        /// <summary>
        /// Applies the header and value to the provided HTTP request message.
        /// </summary>
        /// <param name="request">The HTTP request message.</param>
        public async Task AuthenticateRequestAsync(HttpRequestMessage request)
        {
            var header = await this._header().ConfigureAwait(false);
            var value = await this._value().ConfigureAwait(false);
            request.Headers.Add(header, value);
        }
    }

    #endregion

    public Example24_OpenApiPlugin_Jira(ITestOutputHelper output) : base(output)
    {
<<<<<<< div
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< div
>>>>>>> main
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
>>>>>>> head
    }
}

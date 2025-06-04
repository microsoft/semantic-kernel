// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http.Headers;
using System.Text;
using System.Text.Json;
using Microsoft.Identity.Client;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.OpenApi;

namespace Plugins;

public class CreatePluginFromOpenApiSpec_Jira(ITestOutputHelper output) : BaseTest(output)
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
    /// 4. Configure the secrets as described by the ReadMe.md in the dotnet/samples/Concepts folder.
    /// </summary>
    [Fact(Skip = "Setup credentials")]
    public async Task RunAsync()
    {
        Kernel kernel = new();

        // Change <your-domain> to a jira instance you have access to with your authentication credentials
        string serverUrl = $"https://{TestConfiguration.Jira.Domain}.atlassian.net/rest/api/latest/";

        KernelPlugin jiraFunctions;
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
            var apiPluginFile = "./../../../../Plugins/JiraPlugin/openapi.json";
            jiraFunctions = await kernel.ImportPluginFromOpenApiAsync(
                "jiraPlugin",
                apiPluginFile,
                new OpenApiFunctionExecutionParameters(
                    authCallback: tokenProvider.AuthenticateRequestAsync,
                    serverUrlOverride: new Uri(serverUrl)
                )
            );
        }
        else
        {
            var apiPluginRawFileURL = new Uri("https://raw.githubusercontent.com/microsoft/PowerPlatformConnectors/dev/certified-connectors/JIRA/apiDefinition.swagger.json");
            jiraFunctions = await kernel.ImportPluginFromOpenApiAsync(
                "jiraPlugin",
                apiPluginRawFileURL,
                new OpenApiFunctionExecutionParameters(
                    httpClient, tokenProvider.AuthenticateRequestAsync,
                    serverUrlOverride: new Uri(serverUrl)
                )
            );
        }

        var arguments = new KernelArguments
        {
            // GetIssue Function
            // Set Properties for the Get Issue operation in the openAPI.swagger.json
            // Make sure the issue exists in your Jira instance or it will return a 404
            ["issueKey"] = "TEST-1"
        };

        // Run operation via the semantic kernel
        var result = await kernel.InvokeAsync(jiraFunctions["GetIssue"], arguments);

        Console.WriteLine("\n\n\n");
        var formattedContent = JsonSerializer.Serialize(
            result.GetValue<RestApiOperationResponse>(), s_jsonOptionsCache);
        Console.WriteLine($"GetIssue jiraPlugin response: \n{formattedContent}");

        // AddComment Function
        arguments["issueKey"] = "TEST-2";
        arguments[RestApiOperation.PayloadArgumentName] = """{"body": "Here is a rad comment"}""";

        // Run operation via the semantic kernel
        result = await kernel.InvokeAsync(jiraFunctions["AddComment"], arguments);

        Console.WriteLine("\n\n\n");

        formattedContent = JsonSerializer.Serialize(result.GetValue<RestApiOperationResponse>(), s_jsonOptionsCache);
        Console.WriteLine($"AddComment jiraPlugin response: \n{formattedContent}");
    }

    #region Example of authentication providers

    /// <summary>
    /// Retrieves authentication content (e.g. username/password, API key) via the provided delegate and
    /// applies it to HTTP requests using the "basic" authentication scheme.
    /// </summary>
    public class BasicAuthenticationProvider(Func<Task<string>> credentials)
    {
        private readonly Func<Task<string>> _credentials = credentials;

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
    public class BearerAuthenticationProvider(Func<Task<string>> bearerToken)
    {
        private readonly Func<Task<string>> _bearerToken = bearerToken;

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
    public class InteractiveMsalAuthenticationProvider(string clientId, string tenantId, string[] scopes, Uri redirectUri) : BearerAuthenticationProvider(() => GetTokenAsync(clientId, tenantId, scopes, redirectUri))
    {
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
            {
                result = await app.AcquireTokenSilent(scopes, accounts.FirstOrDefault())
                    .ExecuteAsync().ConfigureAwait(false);
            }
            catch (MsalUiRequiredException)
            {
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
    public sealed class CustomAuthenticationProvider(Func<Task<string>> header, Func<Task<string>> value)
    {
        private readonly Func<Task<string>> _header = header;
        private readonly Func<Task<string>> _value = value;

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
}

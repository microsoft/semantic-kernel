// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http.Headers;
using System.Web;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors.CredentialManagers;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Microsoft.SemanticKernel.Plugins.OpenApi.Extensions;

namespace Plugins;

/// <summary>
/// These examples demonstrate how to use API Manifest plugins to call Microsoft Graph and NASA APIs.
/// API Manifest plugins are created from the OpenAPI document and the manifest file.
/// The manifest file contains the API dependencies and their execution parameters.
/// The manifest file also contains the authentication information for the APIs, however this is not used by the extension method and MUST be setup separately at the moment, which the example demonstrates.
///
/// Important stages being demonstrated:
/// 1. Load APIManifest plugins
/// 2. Configure authentication for the APIs
/// 3. Call functions from the loaded plugins
///
/// Running this test requires the following configuration in `dotnet\samples\Concepts\bin\Debug\net10.0\appsettings.Development.json`:
///
/// ```json
/// {
///  "MSGraph": {
///    "ClientId": "clientId",
///    "TenantId": "tenantId",
///    "Scopes": [
///      "Calendars.Read",
///      "Contacts.Read",
///      "Files.Read.All",
///      "Mail.Read",
///      "User.Read"
///    ],
///    "RedirectUri": "http://localhost"
///  }
/// }
///```
///
/// Replace the clientId and TenantId by your own values.
///
/// To create the application registration:
/// 1. Go to https://aad.portal.azure.com
/// 2. Select create a new application registration
/// 3. Select new public client (add the redirect URI).
/// 4. Navigate to API access, add the listed Microsoft Graph delegated scopes.
/// 5. Grant consent after adding the scopes.
///
/// During the first run, your browser will open to get the token.
///
/// </summary>
/// <param name="output">The output helper to use to the test can emit status information</param>
public class ApiManifestBasedPlugins(ITestOutputHelper output) : BaseTest(output)
{
    private static readonly PromptExecutionSettings s_promptExecutionSettings = new()
    {
        FunctionChoiceBehavior = FunctionChoiceBehavior.Auto(
                    options: new FunctionChoiceBehaviorOptions
                    {
                        AllowStrictSchemaAdherence = true
                    }
                )
    };
    public static readonly IEnumerable<object[]> s_parameters =
    [
        // function names are sanitized operationIds from the OpenAPI document
        ["MessagesPlugin", "me_ListMessages", new KernelArguments(s_promptExecutionSettings) { { "_top", "1" } }, "MessagesPlugin"],
        ["DriveItemPlugin", "drive_root_GetChildrenContent", new KernelArguments(s_promptExecutionSettings) { { "driveItem-Id", "test.txt" } }, "DriveItemPlugin", "MessagesPlugin"],
        ["ContactsPlugin", "me_ListContacts", new KernelArguments(s_promptExecutionSettings) { { "_count", "true" } }, "ContactsPlugin", "MessagesPlugin"],
        ["CalendarPlugin", "me_calendar_ListEvents", new KernelArguments(s_promptExecutionSettings) { { "_top", "1" } }, "CalendarPlugin", "MessagesPlugin"],

        #region Multiple API dependencies (multiple auth requirements) scenario within the same plugin
        // Graph API uses MSAL
        ["AstronomyPlugin", "me_ListMessages", new KernelArguments(s_promptExecutionSettings) { { "_top", "1" } }, "AstronomyPlugin"],
        // Astronomy API uses API key authentication
        ["AstronomyPlugin", "apod", new KernelArguments(s_promptExecutionSettings) { { "_date", "2022-02-02" } }, "AstronomyPlugin"],
        #endregion
    ];

    [Theory, MemberData(nameof(s_parameters))]
    public async Task RunApiManifestPluginAsync(string pluginToTest, string functionToTest, KernelArguments? arguments, params string[] pluginsToLoad)
    {
        WriteSampleHeadingToConsole(pluginToTest, functionToTest, arguments, pluginsToLoad);
        var kernel = Kernel.CreateBuilder().Build();
        await AddApiManifestPluginsAsync(kernel, pluginsToLoad);

        var result = await kernel.InvokeAsync(pluginToTest, functionToTest, arguments);
        Console.WriteLine("--------------------");
        Console.WriteLine($"\nResult:\n{result}\n");
        Console.WriteLine("--------------------");
    }

    private void WriteSampleHeadingToConsole(string pluginToTest, string functionToTest, KernelArguments? arguments, params string[] pluginsToLoad)
    {
        Console.WriteLine();
        Console.WriteLine("======== [ApiManifest Plugins Sample] ========");
        Console.WriteLine($"======== Loading Plugins: {string.Join(" ", pluginsToLoad)} ========");
        Console.WriteLine($"======== Calling Plugin Function: {pluginToTest}.{functionToTest} with parameters {arguments?.Select(x => x.Key + " = " + x.Value).Aggregate((x, y) => x + ", " + y)} ========");
        Console.WriteLine();
    }

    private async Task AddApiManifestPluginsAsync(Kernel kernel, params string[] pluginNames)
    {
#pragma warning disable SKEXP0050
        if (TestConfiguration.MSGraph.Scopes is null)
        {
            throw new InvalidOperationException("Missing Scopes configuration for Microsoft Graph API.");
        }

        LocalUserMSALCredentialManager credentialManager = await LocalUserMSALCredentialManager.CreateAsync().ConfigureAwait(false);

        var token = await credentialManager.GetTokenAsync(
                        TestConfiguration.MSGraph.ClientId,
                        TestConfiguration.MSGraph.TenantId,
                        TestConfiguration.MSGraph.Scopes.ToArray(),
                        TestConfiguration.MSGraph.RedirectUri).ConfigureAwait(false);
#pragma warning restore SKEXP0050

        BearerAuthenticationProviderWithCancellationToken authenticationProvider = new(() => Task.FromResult(token));
#pragma warning disable SKEXP0040

        // Microsoft Graph API execution parameters
        var graphOpenApiFunctionExecutionParameters = new OpenApiFunctionExecutionParameters(
            authCallback: authenticationProvider.AuthenticateRequestAsync,
            serverUrlOverride: new Uri("https://graph.microsoft.com/v1.0"),
            enableDynamicOperationPayload: false,
            enablePayloadNamespacing: false);

        // NASA API execution parameters
        var nasaOpenApiFunctionExecutionParameters = new OpenApiFunctionExecutionParameters(
            authCallback: async (request, cancellationToken) =>
            {
                var uriBuilder = new UriBuilder(request.RequestUri ?? throw new InvalidOperationException("The request URI is null."));
                var query = HttpUtility.ParseQueryString(uriBuilder.Query);
                query["api_key"] = "DEMO_KEY";
                uriBuilder.Query = query.ToString();
                request.RequestUri = uriBuilder.Uri;
            },
            enableDynamicOperationPayload: false,
            enablePayloadNamespacing: false);

        var apiManifestPluginParameters = new ApiManifestPluginParameters(
            functionExecutionParameters: new()
            {
                { "microsoft.graph", graphOpenApiFunctionExecutionParameters },
                { "nasa", nasaOpenApiFunctionExecutionParameters }
            });
        var manifestLookupDirectory = Path.Combine(Directory.GetCurrentDirectory(), "..", "..", "..", "Resources", "Plugins", "ApiManifestPlugins");

        foreach (var pluginName in pluginNames)
        {
            try
            {
                KernelPlugin plugin =
                await kernel.ImportPluginFromApiManifestAsync(
                    pluginName,
                    Path.Combine(manifestLookupDirectory, pluginName, "apimanifest.json"),
                    apiManifestPluginParameters)
                    .ConfigureAwait(false);
                Console.WriteLine($">> {pluginName} is created.");
#pragma warning restore SKEXP0040
            }
            catch (Exception ex)
            {
                kernel.LoggerFactory.CreateLogger("Plugin Creation").LogError(ex, "Plugin creation failed. Message: {0}", ex.Message);
                throw new AggregateException($"Plugin creation failed for {pluginName}", ex);
            }
        }
    }
}

/// <summary>
/// Retrieves a token via the provided delegate and applies it to HTTP requests using the
/// "bearer" authentication scheme.
/// </summary>
public class BearerAuthenticationProviderWithCancellationToken(Func<Task<string>> bearerToken)
{
    private readonly Func<Task<string>> _bearerToken = bearerToken;

    /// <summary>
    /// Applies the token to the provided HTTP request message.
    /// </summary>
    /// <param name="request">The HTTP request message.</param>
    /// <param name="cancellationToken"></param>
    public async Task AuthenticateRequestAsync(HttpRequestMessage request, CancellationToken cancellationToken = default)
    {
        var token = await this._bearerToken().ConfigureAwait(false);
        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
    }
}

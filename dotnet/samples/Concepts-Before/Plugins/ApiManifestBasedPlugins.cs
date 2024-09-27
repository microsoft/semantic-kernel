// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http.Headers;
using System.Web;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors.CredentialManagers;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Microsoft.SemanticKernel.Plugins.OpenApi.Extensions;

namespace Plugins;

// This example shows how to use the ApiManifest based plugins
public class ApiManifestBasedPlugins(ITestOutputHelper output) : BaseTest(output)
{
    public static readonly IEnumerable<object[]> s_parameters =
    [
        // function names are sanitized operationIds from the OpenAPI document
        ["MessagesPlugin", "meListMessages", new KernelArguments { { "_top", "1" } }, "MessagesPlugin"],
        ["DriveItemPlugin", "driverootGetChildrenContent", new KernelArguments { { "driveItem-Id", "test.txt" } }, "DriveItemPlugin", "MessagesPlugin"],
        ["ContactsPlugin", "meListContacts", new KernelArguments() { { "_count", "true" } }, "ContactsPlugin", "MessagesPlugin"],
        ["CalendarPlugin", "mecalendarListEvents", new KernelArguments() { { "_top", "1" } }, "CalendarPlugin", "MessagesPlugin"],

        #region Multiple API dependencies (multiple auth requirements) scenario within the same plugin
        // Graph API uses MSAL
        ["AstronomyPlugin", "meListMessages", new KernelArguments { { "_top", "1" } }, "AstronomyPlugin"],
        // Astronomy API uses API key authentication
        ["AstronomyPlugin", "apod", new KernelArguments { { "_date", "2022-02-02" } }, "AstronomyPlugin"],
        #endregion
    ];

    [Theory, MemberData(nameof(s_parameters))]
    public async Task RunSampleWithPlannerAsync(string pluginToTest, string functionToTest, KernelArguments? arguments, params string[] pluginsToLoad)
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
#pragma warning disable SKEXP0043

        // Microsoft Graph API execution parameters
        var graphOpenApiFunctionExecutionParameters = new OpenApiFunctionExecutionParameters(
            authCallback: authenticationProvider.AuthenticateRequestAsync,
            serverUrlOverride: new Uri("https://graph.microsoft.com/v1.0"));

        // NASA API execution parameters
        var nasaOpenApiFunctionExecutionParameters = new OpenApiFunctionExecutionParameters(
            authCallback: async (request, cancellationToken) =>
            {
                var uriBuilder = new UriBuilder(request.RequestUri ?? throw new InvalidOperationException("The request URI is null."));
                var query = HttpUtility.ParseQueryString(uriBuilder.Query);
                query["api_key"] = "DEMO_KEY";
                uriBuilder.Query = query.ToString();
                request.RequestUri = uriBuilder.Uri;
            });

        var apiManifestPluginParameters = new ApiManifestPluginParameters(
            functionExecutionParameters: new()
            {
                { "microsoft.graph", graphOpenApiFunctionExecutionParameters },
                { "nasa", nasaOpenApiFunctionExecutionParameters }
            });

        foreach (var pluginName in pluginNames)
        {
            try
            {
                KernelPlugin plugin =
                await kernel.ImportPluginFromApiManifestAsync(
                    pluginName,
                    $"Plugins/ApiManifestPlugins/{pluginName}/apimanifest.json",
                    apiManifestPluginParameters)
                    .ConfigureAwait(false);
                Console.WriteLine($">> {pluginName} is created.");
#pragma warning restore SKEXP0040
#pragma warning restore SKEXP0043
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

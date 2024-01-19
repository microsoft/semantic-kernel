// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors.CredentialManagers;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;
using Xunit.Abstractions;
namespace Examples;

// This example shows how to use the ApiManifest based plugins
public class Example99_ApiManifest : BaseTest
{
    private static Kernel? s_kernel;
    private static readonly FunctionCallingStepwisePlanner s_planner = new(s_plannerConfig);
    private static readonly FunctionCallingStepwisePlannerConfig s_plannerConfig = new()
    {
        MaxIterations = 15,
        MaxTokens = 32000
    };

    /// <summary>
    /// Show how to create API Manifest plugins and use them towards a goal.
    /// </summary>
    private void TestSetup()
    {
        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string chatDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string chatModelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;

        if (apiKey == null || chatDeploymentName == null || chatModelId == null || endpoint == null)
        {
            this.WriteLine("Azure endpoint, apiKey, deploymentName, or modelId not found. Skipping example.");
            return;
        }

        s_kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: chatDeploymentName,
                endpoint: endpoint,
                serviceId: "AzureOpenAIChat",
                apiKey: apiKey,
                modelId: chatModelId)
            .Build();
    }

    private void WriteSampleHeadingToConsole(string goal, string expectedOutputDescription, params string[] pluginNames)
    {
        this.WriteLine();
        this.WriteLine($"======== [ApiManifest Plugins] Create and Execute \"{goal}\" Plan ========");
        this.WriteLine($"======== Plugins: {string.Join(" ", pluginNames)} ========");
        this.WriteLine($"======== Expected Output: {expectedOutputDescription} ========");
        this.WriteLine();
    }

    [Theory]
    [InlineData("show the subject of my first message", "latest email message subject is shown", "MessagesPlugin")]
    [InlineData("get contents of file with id=test.txt", "test.txt file is fetched and the content is shown", "DriveItemPlugin", "MessagesPlugin")]
    [InlineData("get contents of file with id=test.txt", "test.txt file is not fetched because DriveItemPlugin is not loaded", "MessagesPlugin")]
    [InlineData("tell me how many contacts I have", "number of contacts is shown", "MessagesPlugin", "ContactsPlugin")]
    [InlineData("tell me title of first event in my calendar", "title of first event from calendar is shown if exists", "MessagesPlugin", "CalendarPlugin")]
    public async Task RunSampleWithPlannerAsync(string goal, string expectedOutputDescription, params string[] pluginNames)
    {
        _ = s_kernel ?? throw new KernelException("Kernel not initialized!");
        WriteSampleHeadingToConsole(goal, expectedOutputDescription, pluginNames);
        s_kernel.Plugins.Clear();
        await AddApiManifestPluginsAsync(pluginNames);

        var result = await s_planner.ExecuteAsync(s_kernel, goal);

        this.WriteLine("--------------------");
        this.WriteLine($"\nResult:\n{result.FinalAnswer}\n");
        this.WriteLine("--------------------");
    }

    private async Task AddApiManifestPluginsAsync(params string[] pluginNames)
    {
        _ = s_kernel ?? throw new KernelException("Kernel not initialized!");
#pragma warning disable SKEXP0053
        if (TestConfiguration.MSGraph.Scopes == null)
        {
            throw new InvalidOperationException("Missing Scopes configuration for Microsoft Graph API.");
        }

        string? currentAssemblyDirectory = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
        if (string.IsNullOrWhiteSpace(currentAssemblyDirectory))
        {
            throw new InvalidOperationException("Unable to determine current assembly directory.");
        }

        LocalUserMSALCredentialManager credentialManager = await LocalUserMSALCredentialManager.CreateAsync().ConfigureAwait(false);

        var token = await credentialManager.GetTokenAsync(
                        TestConfiguration.MSGraph.ClientId,
                        TestConfiguration.MSGraph.TenantId,
                        TestConfiguration.MSGraph.Scopes.ToArray(),
                        TestConfiguration.MSGraph.RedirectUri).ConfigureAwait(false);
#pragma warning restore SKEXP0053

        BearerAuthenticationProviderWithCancellationToken authenticationProvider = new(() => Task.FromResult(token));

        foreach (var pluginName in pluginNames)
        {
            try
            {
#pragma warning disable SKEXP0042
#pragma warning disable SKEXP0099
                KernelPlugin plugin =
                await s_kernel.ImportPluginFromApiManifestAsync(
                    pluginName,
                    $"ApiManifestPlugins/{pluginName}/apimanifest.json",
                    new OpenApiFunctionExecutionParameters(authCallback: authenticationProvider.AuthenticateRequestAsync
                    , serverUrlOverride: new Uri("https://graph.microsoft.com/v1.0")))
                    .ConfigureAwait(false);
                this.WriteLine($">> {pluginName} is created.");
#pragma warning restore SKEXP0042
#pragma warning restore SKEXP0099
            }
            catch (Exception ex)
            {
                s_kernel.LoggerFactory.CreateLogger("Plugin Creation").LogError(ex, "Plugin creation failed. Message: {0}", ex.Message);
                throw new AggregateException($"Plugin creation failed for {pluginName}", ex);
            }
        }
    }

    public Example99_ApiManifest(ITestOutputHelper output) : base(output)
    {
        TestSetup();
    }
}

/// <summary>
/// Retrieves a token via the provided delegate and applies it to HTTP requests using the
/// "bearer" authentication scheme.
/// </summary>
public class BearerAuthenticationProviderWithCancellationToken
{
    private readonly Func<Task<string>> _bearerToken;

    /// <summary>
    /// Creates an instance of the <see cref="BearerAuthenticationProviderWithCancellationToken"/> class.
    /// </summary>
    /// <param name="bearerToken">Delegate to retrieve the bearer token.</param>
    public BearerAuthenticationProviderWithCancellationToken(Func<Task<string>> bearerToken)
    {
        this._bearerToken = bearerToken;
    }

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

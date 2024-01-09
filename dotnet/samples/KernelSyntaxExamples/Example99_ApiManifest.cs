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
using Microsoft.SemanticKernel.Planning.Handlebars;
using Microsoft.SemanticKernel.Plugins.MsGraph.Connectors.CredentialManagers;
using Microsoft.SemanticKernel.Plugins.OpenApi;

// This example shows how to use the Handlebars sequential planner.
public static class Example99_ApiManifest
{
    private static int s_sampleIndex;

    /// <summary>
    /// Show how to create a plan with Handlebars and execute it.
    /// </summary>
    public static async Task RunAsync()
    {
        s_sampleIndex = 1;

        await RunSampleWithPlannerAsync("get my first message", shouldPrintPrompt: false, "MessagesPlugin").ConfigureAwait(false);

        await RunSampleAsync("MessagesPlugin", "Getmemessages", new KernelArguments
        {
           { "_top", "1" }
        }).ConfigureAwait(false);
    }

    private static void WriteSampleHeadingToConsole(string name)
    {
        Console.WriteLine($"======== [ApiManifest Plugins] Sample {s_sampleIndex++} - Create and Execute \"{name}\" Plan ========");
    }

    private static async Task RunSampleAsync(string pluginName, string functionName, KernelArguments arguments)
    {
        var kernel = Kernel.CreateBuilder()
            .Build();

        await AddApiManifestPluginsAsync(kernel, pluginName).ConfigureAwait(false);

        WriteSampleHeadingToConsole($"{pluginName}.{functionName}");
        var result = await kernel.InvokeAsync(pluginName, functionName, arguments).ConfigureAwait(false);
#pragma warning disable SKEXP0042
        Console.WriteLine(result.GetValue<RestApiOperationResponse>()?.Content);
#pragma warning restore SKEXP0042
    }

    private static async Task RunSampleWithPlannerAsync(string goal, bool shouldPrintPrompt = false, params string[] pluginNames)
    {
        string apiKey = TestConfiguration.AzureOpenAI.ApiKey;
        string chatDeploymentName = TestConfiguration.AzureOpenAI.ChatDeploymentName;
        string chatModelId = TestConfiguration.AzureOpenAI.ChatModelId;
        string endpoint = TestConfiguration.AzureOpenAI.Endpoint;

        if (apiKey == null || chatDeploymentName == null || chatModelId == null || endpoint == null)
        {
            Console.WriteLine("Azure endpoint, apiKey, deploymentName, or modelId not found. Skipping example.");
            return;
        }

        var kernel = Kernel.CreateBuilder()
            .AddAzureOpenAIChatCompletion(
                deploymentName: chatDeploymentName,
                endpoint: endpoint,
                serviceId: "AzureOpenAIChat",
                apiKey: apiKey,
                modelId: chatModelId)
            .Build();

        await AddApiManifestPluginsAsync(kernel, pluginNames).ConfigureAwait(false);

        // Use gpt-4 or newer models if you want to test with loops. 
        // Older models like gpt-35-turbo are less recommended. They do handle loops but are more prone to syntax errors.
        var allowLoopsInPlan = chatDeploymentName.Contains("gpt-4", StringComparison.OrdinalIgnoreCase);
        var planner = new HandlebarsPlanner(
            new HandlebarsPlannerOptions()
            {
                // Change this if you want to test with loops regardless of model selection.
                AllowLoops = allowLoopsInPlan
            });

        WriteSampleHeadingToConsole($"{goal}");

        // Create the plan
        var plan = await planner.CreatePlanAsync(kernel, goal);

        // Print the prompt template
        if (shouldPrintPrompt && plan.Prompt is not null)
        {
            Console.WriteLine($"\nPrompt template:\n{plan.Prompt}");
        }

        Console.WriteLine($"\nOriginal plan:\n{plan}");

        // Execute the plan
        var result = await plan.InvokeAsync(kernel);
        Console.WriteLine($"\nResult:\n{result}\n");
    }

    private static async Task AddApiManifestPluginsAsync(Kernel sk, params string[] pluginNames)
    {
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
                KernelPlugin plugin =
                await sk.ImportPluginFromApiManifestAsync(
                    pluginName,
                    $"ApiManifestPlugins/{pluginName}/apimanifest.json",
                    new OpenApiFunctionExecutionParameters(authCallback: authenticationProvider.AuthenticateRequestAsync
                    , serverUrlOverride: new Uri("https://graph.microsoft.com/v1.0")))
                    .ConfigureAwait(false);
#pragma warning restore SKEXP0042
            }
            catch (Exception ex)
            {
                sk.LoggerFactory.CreateLogger("Plugin Creation").LogError(ex, "Plugin creation failed. Message: {0}", ex.Message);
                throw new AggregateException($"Plugin creation failed for {pluginName}", ex);
            }
        }
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

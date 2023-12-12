// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core;
using Azure.Core.Pipeline;
using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example52_ApimAuth
{
    public static async Task RunAsync()
    {
        // Azure API Management details
        // For more information see 'Protect your Azure OpenAI API keys with Azure API Management' here: https://learn.microsoft.com/en-us/semantic-kernel/deploy/
        var apimUri = new Uri(Env.Var("Apim__Endpoint"));
        var subscriptionKey = Env.Var("Apim__SubscriptionKey");

        // Use interactive browser login
        string[] scopes = new string[] { "https://cognitiveservices.azure.com/.default" };
        var credential = new InteractiveBrowserCredential();
        var requestContext = new TokenRequestContext(scopes);
        var accessToken = await credential.GetTokenAsync(requestContext);

        // Create HttpClient and include subscription key as a default header
        var httpClient = new HttpClient();
        httpClient.DefaultRequestHeaders.Add("Ocp-Apim-Subscription-Key", subscriptionKey);

        // Configure OpenAIClient to use
        // - Custom HttpClient with subscription key header
        // - Diagnostics to log error response headers from APIM to aid problem determination
        // - Authentication using BearerTokenCredential retrieved via interactive browser login
        var clientOptions = new OpenAIClientOptions
        {
            Transport = new HttpClientTransport(httpClient),
            Diagnostics =
            {
                LoggedHeaderNames = { "ErrorSource", "ErrorReason", "ErrorMessage", "ErrorScope", "ErrorSection", "ErrorStatusCode" },
            }
        };
        var openAIClient = new OpenAIClient(apimUri, new BearerTokenCredential(accessToken), clientOptions);

        IKernelBuilder builder = Kernel.CreateBuilder();
        builder.Services.AddLogging(c => c.SetMinimumLevel(LogLevel.Warning).AddConsole());
        builder.AddAzureOpenAIChatCompletion(
            deploymentName: TestConfiguration.AzureOpenAI.ChatDeploymentName,
            openAIClient: openAIClient);
        Kernel kernel = builder.Build();

        // Load semantic plugin defined with prompt templates
        string folder = RepoFiles.SamplePluginsPath();

        kernel.ImportPluginFromPromptDirectory(Path.Combine(folder, "FunPlugin"));

        // Run
        var result = await kernel.InvokeAsync(
            kernel.Plugins["FunPlugin"]["Excuses"],
            new() { ["input"] = "I have no homework" }
        );
        Console.WriteLine(result.GetValue<string>());

        httpClient.Dispose();
    }
}

public class BearerTokenCredential : TokenCredential
{
    private readonly AccessToken _accessToken;

    // Constructor that takes a Bearer token string and its expiration date
    public BearerTokenCredential(AccessToken accessToken)
    {
        this._accessToken = accessToken;
    }

    public override AccessToken GetToken(TokenRequestContext requestContext, CancellationToken cancellationToken)
    {
        return this._accessToken;
    }

    public override ValueTask<AccessToken> GetTokenAsync(TokenRequestContext requestContext, CancellationToken cancellationToken)
    {
        return new ValueTask<AccessToken>(this._accessToken);
    }
}

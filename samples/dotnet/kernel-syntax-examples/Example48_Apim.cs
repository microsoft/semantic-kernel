// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Azure.AI.OpenAI;
using Azure.Core.Pipeline;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Azure.Core;
using Azure.Identity;
using System.Threading;
using RepoUtils;

// ReSharper disable once InconsistentNaming
public static class Example48_Apim
{
    public static async Task RunAsync()
    {
        // Azute API Management details
        // For more information see 'Protect your Azure OpenAI API keys with Azure API Management' here: https://learn.microsoft.com/en-us/semantic-kernel/deploy/
        var apimUri = new Uri("https://apim...azure-api.net/");
        var subscriptionKey = "<Add your subscription key here>";

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
        // - Authentication using BearerTokenCredential retrived via interactive browser login
        var clientOptions = new OpenAIClientOptions()
        {
            Transport = new HttpClientTransport(httpClient),
            Diagnostics =
            {
                LoggedHeaderNames = { "ErrorSource", "ErrorReason", "ErrorMessage", "ErrorScope", "ErrorSection", "ErrorStatusCode" },
            }
        };
        var openAIClient = new OpenAIClient(apimUri, new BearerTokenCredential(accessToken), clientOptions);

        // Create logger factory with default level as warning
        using ILoggerFactory loggerFactory = LoggerFactory.Create(builder =>
        {
            builder
                .SetMinimumLevel(LogLevel.Warning)
                .AddConsole();
        });

        // Example: how to use a custom OpenAIClient and configure Azure OpenAI
        var kernel = Kernel.Builder
            .WithLogger(loggerFactory.CreateLogger<IKernel>())
            .WithAzureTextCompletionService("text-davinci-003", openAIClient)
            .Build();

        // Load semantic skill defined with prompt templates
        string folder = RepoFiles.SampleSkillsPath();

        var funSkill = kernel.ImportSemanticSkillFromDirectory(
            folder,
            "FunSkill");

        // Run
        var result = await kernel.RunAsync(
            "I have no homework",
            funSkill["Excuses"]
        );
        Console.WriteLine(result);

        httpClient.Dispose();
    }
}

public class BearerTokenCredential : TokenCredential
{
    private readonly AccessToken _accessToken;

    // Constructor that takes a Bearer token string and its expiration date
    public BearerTokenCredential(AccessToken accessToken)
    {
        _accessToken = accessToken;
    }

    public override AccessToken GetToken(TokenRequestContext requestContext, CancellationToken cancellationToken)
    {
        return _accessToken;
    }

    public override ValueTask<AccessToken> GetTokenAsync(TokenRequestContext requestContext, CancellationToken cancellationToken)
    {
        return new ValueTask<AccessToken>(_accessToken);
    }
}

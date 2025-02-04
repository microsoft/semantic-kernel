// Copyright (c) Microsoft. All rights reserved.

using Azure;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;

namespace AzureAISearchIntegrationTests.Support;

public static class AzureAISearchTestEnvironment
{
    private static SearchIndexClient? s_client;
    private static AzureAISearchVectorStore? s_defaultVectorStore;

    public static SearchIndexClient Client
        => s_client ?? throw new InvalidOperationException("Call InitializeAsync() first");

    public static AzureAISearchVectorStore DefaultVectorStore
        => s_defaultVectorStore ?? throw new InvalidOperationException("Call InitializeAsync() first");

    private static readonly string? s_serviceUrl, s_apiKey;

    public static bool IsConnectionInfoDefined => s_serviceUrl is not null && s_apiKey is not null;

    static AzureAISearchTestEnvironment()
    {
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true)
            .AddEnvironmentVariables()
            .AddUserSecrets<AzureAISearchUrlRequiredAttribute>()
            .Build();

        var azureAISearchSection = configuration.GetSection("AzureAISearch");
        s_serviceUrl = azureAISearchSection?["ServiceUrl"];
        s_apiKey = azureAISearchSection?["ApiKey"];
    }

    public static async Task InitializeAsync()
    {
        if (s_client is not null)
        {
            return;
        }

        if (string.IsNullOrWhiteSpace(s_serviceUrl) || string.IsNullOrWhiteSpace(s_apiKey))
        {
            throw new InvalidOperationException("Service URL and API key are not configured, set AzureAISearch:ServiceUrl and AzureAISearch:ApiKey");
        }

        s_client = new SearchIndexClient(new Uri(s_serviceUrl), new AzureKeyCredential(s_apiKey));
        s_defaultVectorStore = new(s_client);
    }
}

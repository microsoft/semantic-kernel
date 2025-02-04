// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

namespace CosmosNoSQLIntegrationTests.Support;

public static class CosmosTestEnvironment
{
    private static CosmosClient? s_client;
    private static Database? s_database;
    private static AzureCosmosDBNoSQLVectorStore? s_defaultVectorStore;

    public static CosmosClient Client
        => s_client ?? throw new InvalidOperationException("Call InitializeAsync() first");

    public static AzureCosmosDBNoSQLVectorStore DefaultVectorStore
        => s_defaultVectorStore ?? throw new InvalidOperationException("Call InitializeAsync() first");

    private static readonly string? s_connectionString;

    public static bool IsConnectionStringDefined => s_connectionString is not null;

    static CosmosTestEnvironment()
    {
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true)
            .AddEnvironmentVariables()
            .Build();

        s_connectionString = configuration["AzureCosmosDBNoSQL:ConnectionString"];
    }

    public static async Task InitializeAsync()
    {
        if (s_client is not null)
        {
            return;
        }

        if (string.IsNullOrWhiteSpace(s_connectionString))
        {
            throw new InvalidOperationException("Connection string is not configured, set the AzureCosmosDBNoSQL:ConnectionString environment variable");
        }

        var options = new CosmosClientOptions
        {
            UseSystemTextJsonSerializerWithOptions = JsonSerializerOptions.Default,
            ConnectionMode = ConnectionMode.Gateway,
            HttpClientFactory = () => new HttpClient(new HttpClientHandler { ServerCertificateCustomValidationCallback = HttpClientHandler.DangerousAcceptAnyServerCertificateValidator })
        };

        s_client = new CosmosClient(s_connectionString, options);
        s_database = s_client.GetDatabase("VectorDataIntegrationTests");
        await s_client.CreateDatabaseIfNotExistsAsync("VectorDataIntegrationTests");
        s_defaultVectorStore = new(s_database);
    }
}

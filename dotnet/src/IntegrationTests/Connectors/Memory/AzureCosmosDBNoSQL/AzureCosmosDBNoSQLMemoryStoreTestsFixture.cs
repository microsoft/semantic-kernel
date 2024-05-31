// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.Configuration;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.AzureCosmosDBNoSQL;

public class AzureCosmosDBNoSQLMemoryStoreTestsFixture : IAsyncLifetime
{
    public AzureCosmosDBNoSQLMemoryStore MemoryStore { get; }
    public string DatabaseName { get; }
    public string CollectionName { get; }

    public AzureCosmosDBNoSQLMemoryStoreTestsFixture()
    {
        // Load Configuration
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(
                path: "testsettings.development.json",
                optional: false,
                reloadOnChange: true
            )
            .AddEnvironmentVariables()
            .Build();

        var connectionString = GetSetting(configuration, "ConnectionString");
        this.DatabaseName = "DotNetSKTestDB";
        this.CollectionName = "DotNetSKTestCollection";
        this.MemoryStore = new AzureCosmosDBNoSQLMemoryStore(
            connectionString,
            this.DatabaseName,
            new VectorEmbeddingPolicy(
                new Collection<Embedding>
                {
                    new()
                    {
                        DataType = VectorDataType.Float32,
                        Dimensions = 3,
                        DistanceFunction = DistanceFunction.Cosine,
                        Path = "/embedding"
                    }
                }),
            new()
            {
                VectorIndexes = new Collection<VectorIndexPath> {
                    new()
                    {
                        Path = "/embedding",
                        Type = VectorIndexType.Flat,
                    },
                },
            }
        );
    }

    public Task InitializeAsync()
        => Task.CompletedTask;

    public Task DisposeAsync()
        => Task.CompletedTask;

    private static string GetSetting(IConfigurationRoot configuration, string settingName)
    {
        var settingValue = configuration[$"AzureCosmosDB:{settingName}"];
        if (string.IsNullOrWhiteSpace(settingValue))
        {
            throw new ArgumentNullException($"{settingValue} string is not configured");
        }

        return settingValue;
    }
}

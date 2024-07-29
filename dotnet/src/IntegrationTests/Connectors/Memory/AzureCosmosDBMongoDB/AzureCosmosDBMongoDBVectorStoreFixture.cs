// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Configuration;
using MongoDB.Driver;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.AzureCosmosDBMongoDB;

public class AzureCosmosDBMongoDBVectorStoreFixture : IAsyncLifetime
{
    public IMongoDatabase MongoDatabase { get; }

    public AzureCosmosDBMongoDBVectorStoreFixture()
    {
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: false, reloadOnChange: true)
            .AddJsonFile(
                path: "testsettings.development.json",
                optional: false,
                reloadOnChange: true
            )
            .AddEnvironmentVariables()
            .Build();

        var connectionString = GetConnectionString(configuration);
        var client = new MongoClient(connectionString);

        this.MongoDatabase = client.GetDatabase("test");
    }

    public async Task InitializeAsync()
    {
        await this.MongoDatabase.CreateCollectionAsync("hotels");
        await this.MongoDatabase.CreateCollectionAsync("contacts");
        await this.MongoDatabase.CreateCollectionAsync("addresses");
    }

    public Task DisposeAsync() => Task.CompletedTask;

    #region private

    private static string GetConnectionString(IConfigurationRoot configuration)
    {
        var settingValue = configuration["AzureCosmosDBMongoDB:ConnectionString"];
        if (string.IsNullOrWhiteSpace(settingValue))
        {
            throw new ArgumentNullException($"{settingValue} string is not configured");
        }

        return settingValue;
    }

    #endregion
}

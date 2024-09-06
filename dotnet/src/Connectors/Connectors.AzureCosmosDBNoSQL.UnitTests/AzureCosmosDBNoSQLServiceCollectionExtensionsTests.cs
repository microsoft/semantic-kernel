// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Http;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.AzureCosmosDBNoSQL.UnitTests;

/// <summary>
/// Unit tests for <see cref="AzureCosmosDBNoSQLServiceCollectionExtensions"/> class.
/// </summary>
public sealed class AzureCosmosDBNoSQLServiceCollectionExtensionsTests
{
    private readonly IServiceCollection _serviceCollection = new ServiceCollection();

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange
        var cosmosClientOptions = new CosmosClientOptions();
        var cosmosClientMock = new Mock<CosmosClient>();
        var databaseMock = new Mock<Database>();

        cosmosClientMock.SetupGet(c => c.ClientOptions).Returns(cosmosClientOptions);
        databaseMock.SetupGet(d => d.Client).Returns(cosmosClientMock.Object);

        this._serviceCollection.AddSingleton<Database>(databaseMock.Object);

        // Act
        this._serviceCollection.AddAzureCosmosDBNoSQLVectorStore();

        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<IVectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<AzureCosmosDBNoSQLVectorStore>(vectorStore);
        Assert.Equal(HttpHeaderConstant.Values.UserAgent, cosmosClientOptions.ApplicationName);
    }

    [Fact]
    public void AddVectorStoreWithConnectionStringRegistersClass()
    {
        // Act
        this._serviceCollection.AddAzureCosmosDBNoSQLVectorStore("AccountEndpoint=https://test.documents.azure.com:443/;AccountKey=mock;", "mydb");

        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<IVectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<AzureCosmosDBNoSQLVectorStore>(vectorStore);
        var database = (Database)vectorStore.GetType().GetField("_database", BindingFlags.NonPublic | BindingFlags.Instance)!.GetValue(vectorStore)!;
        Assert.Equal(HttpHeaderConstant.Values.UserAgent, database.Client.ClientOptions.ApplicationName);
    }
}

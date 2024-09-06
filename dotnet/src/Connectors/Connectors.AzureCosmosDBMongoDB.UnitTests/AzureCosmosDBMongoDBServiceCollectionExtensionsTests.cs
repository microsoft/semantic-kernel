// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Http;
using MongoDB.Driver;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.AzureCosmosDBMongoDB.UnitTests;

/// <summary>
/// Unit tests for <see cref="AzureCosmosDBMongoDBServiceCollectionExtensions"/> class.
/// </summary>
public sealed class AzureCosmosDBMongoDBServiceCollectionExtensionsTests
{
    private readonly IServiceCollection _serviceCollection = new ServiceCollection();

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange
        var mongoClientSettings = new MongoClientSettings();
        var mongoClient = new Mock<IMongoClient>();
        var databaseMock = new Mock<IMongoDatabase>();

        mongoClient.SetupGet(c => c.Settings).Returns(mongoClientSettings);
        databaseMock.SetupGet(d => d.Client).Returns(mongoClient.Object);

        this._serviceCollection.AddSingleton<IMongoDatabase>(databaseMock.Object);

        // Act
        this._serviceCollection.AddAzureCosmosDBMongoDBVectorStore();

        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<IVectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<AzureCosmosDBMongoDBVectorStore>(vectorStore);
        Assert.Equal(HttpHeaderConstant.Values.UserAgent, mongoClientSettings.ApplicationName);
    }

    [Fact]
    public void AddVectorStoreWithConnectionStringRegistersClass()
    {
        // Act
        this._serviceCollection.AddAzureCosmosDBMongoDBVectorStore("mongodb://localhost:27017", "mydb");

        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<IVectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<AzureCosmosDBMongoDBVectorStore>(vectorStore);

        var database = (IMongoDatabase)vectorStore.GetType().GetField("_mongoDatabase", BindingFlags.NonPublic | BindingFlags.Instance)!.GetValue(vectorStore)!;
        Assert.Equal(HttpHeaderConstant.Values.UserAgent, database.Client.Settings.ApplicationName);
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.CosmosMongoDB;
using Microsoft.SemanticKernel.Http;
using MongoDB.Driver;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.CosmosMongoDB.UnitTests;

/// <summary>
/// Unit tests for <see cref="CosmosMongoServiceCollectionExtensions"/> class.
/// </summary>
public sealed class CosmosMongoServiceCollectionExtensionsTests
{
    private readonly IServiceCollection _serviceCollection = new ServiceCollection();

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange
        this._serviceCollection.AddSingleton<IMongoDatabase>(Mock.Of<IMongoDatabase>());

        // Act
        this._serviceCollection.AddCosmosMongoVectorStore();

        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<VectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<CosmosMongoVectorStore>(vectorStore);
    }

    [Fact]
    public void AddVectorStoreWithConnectionStringRegistersClass()
    {
        // Act
        this._serviceCollection.AddCosmosMongoVectorStore("mongodb://localhost:27017", "mydb");

        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<VectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<CosmosMongoVectorStore>(vectorStore);

        var database = (IMongoDatabase)vectorStore.GetType().GetField("_mongoDatabase", BindingFlags.NonPublic | BindingFlags.Instance)!.GetValue(vectorStore)!;
        Assert.Equal(HttpHeaderConstant.Values.UserAgent, database.Client.Settings.ApplicationName);
    }

    [Fact]
    public void AddVectorStoreRecordCollectionRegistersClass()
    {
        // Arrange
        this._serviceCollection.AddSingleton<IMongoDatabase>(Mock.Of<IMongoDatabase>());

        // Act
        this._serviceCollection.AddCosmosMongoVectorStoreRecordCollection<TestRecord>("testcollection");

        // Assert
        this.AssertVectorStoreRecordCollectionCreated();
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithConnectionStringRegistersClass()
    {
        // Act
        this._serviceCollection.AddCosmosMongoVectorStoreRecordCollection<TestRecord>("testcollection", "mongodb://localhost:27017", "mydb");

        // Assert
        this.AssertVectorStoreRecordCollectionCreated();
    }

    private void AssertVectorStoreRecordCollectionCreated()
    {
        var serviceProvider = this._serviceCollection.BuildServiceProvider();

        var collection = serviceProvider.GetRequiredService<VectorStoreCollection<string, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<CosmosMongoCollection<string, TestRecord>>(collection);

        var vectorizedSearch = serviceProvider.GetRequiredService<IVectorSearchable<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<CosmosMongoCollection<string, TestRecord>>(vectorizedSearch);
    }

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class TestRecord
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [VectorStoreKey]
        public string Id { get; set; } = string.Empty;
    }
}

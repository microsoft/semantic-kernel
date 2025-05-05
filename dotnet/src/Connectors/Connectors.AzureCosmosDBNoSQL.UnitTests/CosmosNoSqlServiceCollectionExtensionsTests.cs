// Copyright (c) Microsoft. All rights reserved.

using System.Reflection;
using System.Text.Json;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Microsoft.SemanticKernel.Http;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.AzureCosmosDBNoSQL.UnitTests;

/// <summary>
/// Unit tests for <see cref="CosmosNoSqlServiceCollectionExtensions"/> class.
/// </summary>
public sealed class CosmosNoSqlServiceCollectionExtensionsTests
{
    private readonly IServiceCollection _serviceCollection = new ServiceCollection();
    private readonly Mock<Database> _mockDatabase = new();

    public CosmosNoSqlServiceCollectionExtensionsTests()
    {
        var mockClient = new Mock<CosmosClient>();

        mockClient.Setup(l => l.ClientOptions).Returns(new CosmosClientOptions() { UseSystemTextJsonSerializerWithOptions = JsonSerializerOptions.Default });

        this._mockDatabase
            .Setup(l => l.Client)
            .Returns(mockClient.Object);
    }

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange
        this._serviceCollection.AddSingleton<Database>(this._mockDatabase.Object);

        // Act
        this._serviceCollection.AddAzureCosmosDBNoSQLVectorStore();

        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<VectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL.CosmosNoSqlVectorStore>(vectorStore);
    }

    [Fact]
    public void AddVectorStoreWithConnectionStringRegistersClass()
    {
        // Act
        this._serviceCollection.AddAzureCosmosDBNoSQLVectorStore("AccountEndpoint=https://test.documents.azure.com:443/;AccountKey=mock;", "mydb");

        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<VectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL.CosmosNoSqlVectorStore>(vectorStore);
        var database = (Database)vectorStore.GetType().GetField("_database", BindingFlags.NonPublic | BindingFlags.Instance)!.GetValue(vectorStore)!;
        Assert.Equal(HttpHeaderConstant.Values.UserAgent, database.Client.ClientOptions.ApplicationName);
    }

    [Fact]
    public void AddVectorStoreRecordCollectionRegistersClass()
    {
        // Arrange
        this._serviceCollection.AddSingleton<Database>(this._mockDatabase.Object);

        // Act
        this._serviceCollection.AddAzureCosmosDBNoSQLVectorStoreRecordCollection<TestRecord>("testcollection");

        // Assert
        this.AssertVectorStoreRecordCollectionCreated();
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithConnectionStringRegistersClass()
    {
        // Act
        this._serviceCollection.AddAzureCosmosDBNoSQLVectorStoreRecordCollection<TestRecord>("testcollection", "AccountEndpoint=https://test.documents.azure.com:443/;AccountKey=mock;", "mydb");

        // Assert
        this.AssertVectorStoreRecordCollectionCreated();
    }

    private void AssertVectorStoreRecordCollectionCreated()
    {
        var serviceProvider = this._serviceCollection.BuildServiceProvider();

        var collection = serviceProvider.GetRequiredService<VectorStoreCollection<string, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<CosmosNoSqlCollection<string, TestRecord>>(collection);

        var vectorizedSearch = serviceProvider.GetRequiredService<IVectorSearchable<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<CosmosNoSqlCollection<string, TestRecord>>(vectorizedSearch);
    }

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class TestRecord
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [VectorStoreKey]
        public string Id { get; set; } = string.Empty;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Data;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.Sqlite.UnitTests;

/// <summary>
/// Unit tests for <see cref="SqliteServiceCollectionExtensions"/> class.
/// </summary>
public sealed class SqliteServiceCollectionExtensionsTests
{
    private readonly IServiceCollection _serviceCollection = new ServiceCollection();

    [Theory]
    [InlineData(ConnectionState.Open)]
    [InlineData(ConnectionState.Closed)]
    public void AddVectorStoreRegistersClass(ConnectionState connectionState)
    {
        // Arrange
        var expectedOpenCalls = connectionState == ConnectionState.Closed ? 1 : 0;

        var mockConnection = new Mock<SqliteConnection>();

        mockConnection.Setup(l => l.State).Returns(connectionState);
        mockConnection.Setup(l => l.Open());

        this._serviceCollection.AddTransient<SqliteConnection>((_) => mockConnection.Object);

        // Act
        this._serviceCollection.AddSqliteVectorStore();

        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<IVectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<SqliteVectorStore>(vectorStore);

        mockConnection.Verify(l => l.Open(), Times.Exactly(expectedOpenCalls));
    }

    [Theory]
    [InlineData(ConnectionState.Open)]
    [InlineData(ConnectionState.Closed)]
    public void AddVectorStoreRecordCollectionWithStringKeyRegistersClass(ConnectionState connectionState)
    {
        // Arrange
        var expectedOpenCalls = connectionState == ConnectionState.Closed ? 1 : 0;

        var mockConnection = new Mock<SqliteConnection>();

        mockConnection.SetupSequence(l => l.State)
            .Returns(connectionState)
            .Returns(ConnectionState.Open);

        mockConnection.Setup(l => l.Open());

        this._serviceCollection.AddTransient<SqliteConnection>((_) => mockConnection.Object);

        // Act
        this._serviceCollection.AddSqliteVectorStoreRecordCollection<string, TestRecord>("testcollection");

        var serviceProvider = this._serviceCollection.BuildServiceProvider();

        // Assert
        var collection = serviceProvider.GetRequiredService<IVectorStoreRecordCollection<string, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<SqliteVectorStoreRecordCollection<TestRecord>>(collection);

        var vectorizedSearch = serviceProvider.GetRequiredService<IVectorizedSearch<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<SqliteVectorStoreRecordCollection<TestRecord>>(vectorizedSearch);

        mockConnection.Verify(l => l.Open(), Times.Exactly(expectedOpenCalls));
    }

    [Theory]
    [InlineData(ConnectionState.Open)]
    [InlineData(ConnectionState.Closed)]
    public void AddVectorStoreRecordCollectionWithNumericKeyRegistersClass(ConnectionState connectionState)
    {
        // Arrange
        var expectedOpenCalls = connectionState == ConnectionState.Closed ? 1 : 0;

        var mockConnection = new Mock<SqliteConnection>();

        mockConnection.SetupSequence(l => l.State)
            .Returns(connectionState)
            .Returns(ConnectionState.Open);

        mockConnection.Setup(l => l.Open());

        this._serviceCollection.AddTransient<SqliteConnection>((_) => mockConnection.Object);

        // Act
        this._serviceCollection.AddSqliteVectorStoreRecordCollection<ulong, TestRecord>("testcollection");

        var serviceProvider = this._serviceCollection.BuildServiceProvider();

        // Assert
        var collection = serviceProvider.GetRequiredService<IVectorStoreRecordCollection<ulong, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<SqliteVectorStoreRecordCollection<TestRecord>>(collection);

        var vectorizedSearch = serviceProvider.GetRequiredService<IVectorizedSearch<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<SqliteVectorStoreRecordCollection<TestRecord>>(vectorizedSearch);

        mockConnection.Verify(l => l.Open(), Times.Exactly(expectedOpenCalls));
    }

    #region private

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class TestRecord
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [VectorStoreRecordKey]
        public string Id { get; set; } = string.Empty;
    }

    #endregion
}

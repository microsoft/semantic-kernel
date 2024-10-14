// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Xunit;

namespace SemanticKernel.Connectors.Sqlite.UnitTests;

/// <summary>
/// Unit tests for <see cref="SqliteVectorStoreRecordCollection{TRecord}"/> class.
/// </summary>
public sealed class SqliteVectorStoreRecordCollectionTests
{
    [Theory]
    [InlineData(1)]
    [InlineData(0)]
    public async Task CollectionExistsReturnsValidResultAsync(long tableCount)
    {
        // Arrange
        const string TableName = "CollectionExists";

        using var fakeCommand = new FakeDbCommand(scalarResult: tableCount);
        using var fakeConnection = new FakeDBConnection(fakeCommand);

        var sut = new SqliteVectorStoreRecordCollection<RecordWithVectorProperty>(fakeConnection, TableName);

        // Act
        var result = await sut.CollectionExistsAsync();

        Assert.Equal(tableCount > 0, result);
    }

    [Fact]
    public async Task CreateCollectionCallsExecuteNonQueryMethodAsync()
    {
        // Arrange
        const string TableName = "CreateCollection";

        using var fakeCommand = new FakeDbCommand();
        using var fakeConnection = new FakeDBConnection(fakeCommand);

        var sut = new SqliteVectorStoreRecordCollection<RecordWithVectorProperty>(fakeConnection, TableName);

        // Act
        await sut.CreateCollectionAsync();

        // Assert
        Assert.Equal(2, fakeCommand.ExecuteNonQueryCallCount);
    }

    [Fact]
    public async Task CreateCollectionIfNotExistsCallsExecuteNonQueryMethodAsync()
    {
        // Arrange
        const string TableName = "CreateCollectionIfNotExists";

        using var fakeCommand = new FakeDbCommand();
        using var fakeConnection = new FakeDBConnection(fakeCommand);

        var sut = new SqliteVectorStoreRecordCollection<RecordWithVectorProperty>(fakeConnection, TableName);

        // Act
        await sut.CreateCollectionIfNotExistsAsync();

        // Assert
        Assert.Equal(2, fakeCommand.ExecuteNonQueryCallCount);
    }

    [Fact]
    public async Task DeleteCollectionCallsExecuteNonQueryMethodAsync()
    {
        // Arrange
        using var fakeCommandWithVectorProperty = new FakeDbCommand();
        using var fakeConnectionWithVectorProperty = new FakeDBConnection(fakeCommandWithVectorProperty);

        using var fakeCommandWithoutVectorProperty = new FakeDbCommand();
        using var fakeConnectionWithoutVectorProperty = new FakeDBConnection(fakeCommandWithoutVectorProperty);

        var collectionWithVectorProperty = new SqliteVectorStoreRecordCollection<RecordWithVectorProperty>(fakeConnectionWithVectorProperty, "WithVectorProperty");
        var collectionWithoutVectorProperty = new SqliteVectorStoreRecordCollection<RecordWithoutVectorProperty>(fakeConnectionWithoutVectorProperty, "WithoutVectorProperty");

        // Act
        await collectionWithVectorProperty.DeleteCollectionAsync();
        await collectionWithoutVectorProperty.DeleteCollectionAsync();

        // Assert
        Assert.Equal(2, fakeCommandWithVectorProperty.ExecuteNonQueryCallCount);
        Assert.Equal(1, fakeCommandWithoutVectorProperty.ExecuteNonQueryCallCount);
    }

    #region private

#pragma warning disable CA1812
    private sealed class RecordWithVectorProperty
    {
        [VectorStoreRecordKey]
        public ulong Key { get; set; }

        [VectorStoreRecordData]
        public string? Text { get; set; }

        [VectorStoreRecordVector(Dimensions: 4, DistanceFunction: DistanceFunction.CosineDistance)]
        public ReadOnlyMemory<float>? Embedding1 { get; set; }
    }

    private sealed class RecordWithoutVectorProperty
    {
        [VectorStoreRecordKey]
        public ulong Key { get; set; }

        [VectorStoreRecordData]
        public string? Text { get; set; }
    }
#pragma warning restore CA1812

    #endregion
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Data.Common;
using System.Linq;
using System.Numerics;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Moq;
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

        var sut = new SqliteVectorStoreRecordCollection<TestRecord>(fakeConnection, TableName);

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

        var sut = new SqliteVectorStoreRecordCollection<TestRecord>(fakeConnection, TableName);

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

        var sut = new SqliteVectorStoreRecordCollection<TestRecord>(fakeConnection, TableName);

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

        var collectionWithVectorProperty = new SqliteVectorStoreRecordCollection<TestRecord>(fakeConnectionWithVectorProperty, "WithVectorProperty");
        var collectionWithoutVectorProperty = new SqliteVectorStoreRecordCollection<RecordWithoutVectorProperty>(fakeConnectionWithoutVectorProperty, "WithoutVectorProperty");

        // Act
        await collectionWithVectorProperty.DeleteCollectionAsync();
        await collectionWithoutVectorProperty.DeleteCollectionAsync();

        // Assert
        Assert.Equal(2, fakeCommandWithVectorProperty.ExecuteNonQueryCallCount);
        Assert.Equal(1, fakeCommandWithoutVectorProperty.ExecuteNonQueryCallCount);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task VectorizedSearchReturnsRecordAsync(bool includeVectors)
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1f, 2f, 3f, 4f]);

        var mockReader = GetDbDataReaderMock(key: 1, data: "Test data", vector: vector);

        mockReader.Setup(l => l.GetOrdinal("distance")).Returns(3);
        mockReader.Setup(l => l.GetFieldValue<double>(3)).Returns(5.5);

        using var fakeCommand = new FakeDbCommand(mockReader.Object);
        using var fakeConnection = new FakeDBConnection(fakeCommand);

        var sut = new SqliteVectorStoreRecordCollection<TestRecord>(fakeConnection, "VectorizedSearch");

        // Act
        var results = await sut.VectorizedSearchAsync(vector, new() { IncludeVectors = includeVectors });
        var result = await results.Results.FirstOrDefaultAsync();

        // Assert
        Assert.NotNull(result);

        var record = result.Record;

        Assert.NotNull(record);

        Assert.Equal(5.5, result.Score);
        Assert.Equal((ulong)1, record.Key);
        Assert.Equal("Test data", record.Text);

        if (includeVectors)
        {
            Assert.NotNull(record.Embedding);
            Assert.Equal(vector.Span.ToArray(), record.Embedding.Value.Span.ToArray());
        }
        else
        {
            Assert.Null(record.Embedding);
        }
    }

    #region private

    private static Mock<DbDataReader> GetDbDataReaderMock(
        long key,
        string data,
        ReadOnlyMemory<float> vector)
    {
        var vectorBytes = SqliteVectorStoreRecordPropertyMapping.MapVectorForStorageModel(vector);

        var mockReader = new Mock<DbDataReader>();
        mockReader
            .SetupSequence(l => l.ReadAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(true)
            .ReturnsAsync(false);

        mockReader.Setup(l => l.IsDBNull(It.IsAny<int>())).Returns(false);

        mockReader.Setup(l => l.GetOrdinal(nameof(TestRecord.Key))).Returns(0);
        mockReader.Setup(l => l.GetOrdinal(nameof(TestRecord.Text))).Returns(1);
        mockReader.Setup(l => l.GetOrdinal(nameof(TestRecord.Embedding))).Returns(2);

        mockReader.Setup(l => l.GetInt64(0)).Returns(key);
        mockReader.Setup(l => l.GetString(1)).Returns(data);
        mockReader.Setup(l => l[2]).Returns(vectorBytes);

        return mockReader;
    }

#pragma warning disable CA1812
    private sealed class TestRecord
    {
        [VectorStoreRecordKey]
        public ulong Key { get; set; }

        [VectorStoreRecordData]
        public string? Text { get; set; }

        [VectorStoreRecordVector(Dimensions: 4, DistanceFunction: DistanceFunction.CosineDistance)]
        public ReadOnlyMemory<float>? Embedding { get; set; }
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

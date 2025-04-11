// Copyright (c) Microsoft. All rights reserved.

// TODO: Reimplement these as integration tests, #10464

#if DISABLED

using System;
using System.Collections.Generic;
using System.Data.Common;
using System.Linq;
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

        var sut = new SqliteVectorStoreRecordCollection<TestRecord<ulong>>(fakeConnection, TableName);

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

        var sut = new SqliteVectorStoreRecordCollection<TestRecord<ulong>>(fakeConnection, TableName);

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

        var sut = new SqliteVectorStoreRecordCollection<TestRecord<ulong>>(fakeConnection, TableName);

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

        var collectionWithVectorProperty = new SqliteVectorStoreRecordCollection<TestRecord<ulong>>(fakeConnectionWithVectorProperty, "WithVectorProperty");
        var collectionWithoutVectorProperty = new SqliteVectorStoreRecordCollection<TestRecordWithoutVectorProperty<ulong>>(fakeConnectionWithoutVectorProperty, "WithoutVectorProperty");

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
        var expectedRecord = new TestRecord<ulong> { Key = 1, Data = "Test data", Vector = new ReadOnlyMemory<float>([1f, 2f, 3f, 4f]) };

        var mockReader = new Mock<DbDataReader>();

        SetupDbDataReaderGetBatch(mockReader, [expectedRecord]);

        mockReader.Setup(l => l.GetOrdinal("distance")).Returns(3);
        mockReader.Setup(l => l.GetFieldValue<double>(3)).Returns(5.5);

        using var fakeCommand = new FakeDbCommand(mockReader.Object);
        using var fakeConnection = new FakeDBConnection(fakeCommand);

        var sut = new SqliteVectorStoreRecordCollection<TestRecord<ulong>>(fakeConnection, "VectorizedSearch");

        // Act
        var result = await sut.VectorizedSearchAsync(expectedRecord.Vector, new() { IncludeVectors = includeVectors }).FirstOrDefaultAsync();

        // Assert
        Assert.NotNull(result);

        Assert.Equal(5.5, result.Score);

        AssertRecord(expectedRecord, result.Record, includeVectors);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetReturnsValidRecordAsync(bool includeVectors)
    {
        // Arrange
        var expectedRecord = new TestRecord<ulong> { Key = 1, Data = "Test data", Vector = new ReadOnlyMemory<float>([1f, 2f, 3f, 4f]) };

        var mockReader = new Mock<DbDataReader>();

        SetupDbDataReaderGetBatch(mockReader, [expectedRecord]);

        using var fakeCommand = new FakeDbCommand(mockReader.Object);
        using var fakeConnection = new FakeDBConnection(fakeCommand);

        var sut = new SqliteVectorStoreRecordCollection<TestRecord<ulong>>(fakeConnection, "Get");

        // Act
        var actualRecord = await sut.GetAsync(expectedRecord.Key, new() { IncludeVectors = includeVectors });

        // Assert
        AssertRecord(expectedRecord, actualRecord, includeVectors);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task GetBatchReturnsValidRecordsAsync(bool includeVectors)
    {
        // Arrange
        var expectedRecord1 = new TestRecord<ulong> { Key = 1, Data = "Test data", Vector = new ReadOnlyMemory<float>([1f, 2f, 3f, 4f]) };
        var expectedRecord2 = new TestRecord<ulong> { Key = 2, Data = "Test data", Vector = new ReadOnlyMemory<float>([1f, 2f, 3f, 4f]) };
        var expectedRecord3 = new TestRecord<ulong> { Key = 3, Data = "Test data", Vector = new ReadOnlyMemory<float>([1f, 2f, 3f, 4f]) };

        var expectedRecords = new List<TestRecord<ulong>> { expectedRecord1, expectedRecord2, expectedRecord3 };

        var mockReader = new Mock<DbDataReader>();

        SetupDbDataReaderGetBatch(mockReader, expectedRecords);

        using var fakeCommand = new FakeDbCommand(mockReader.Object);
        using var fakeConnection = new FakeDBConnection(fakeCommand);

        var sut = new SqliteVectorStoreRecordCollection<TestRecord<ulong>>(fakeConnection, "GetBatch");

        // Act
        var actualRecords = await sut
            .GetBatchAsync(expectedRecords.Select(l => l.Key), new() { IncludeVectors = includeVectors })
            .ToListAsync();

        // Assert
        for (var i = 0; i < actualRecords.Count; i++)
        {
            AssertRecord(expectedRecords[i], actualRecords[i], includeVectors);
        }
    }

    [Fact]
    public async Task UpsertReturnsKeyAsync()
    {
        // Arrange
        var expectedRecord = new TestRecord<ulong> { Key = 1, Data = "Test data", Vector = new ReadOnlyMemory<float>([1f, 2f, 3f, 4f]) };

        var mockReader = new Mock<DbDataReader>();

        SetupDbDataReaderUpsertBatch(mockReader, [expectedRecord.Key]);

        using var fakeCommand = new FakeDbCommand(mockReader.Object);
        using var fakeConnection = new FakeDBConnection(fakeCommand);

        var sut = new SqliteVectorStoreRecordCollection<TestRecord<ulong>>(fakeConnection, "Upsert");

        // Act
        var actualKey = await sut.UpsertAsync(expectedRecord);

        // Assert
        Assert.Equal(expectedRecord.Key, actualKey);

        Assert.Equal(2, fakeCommand.ExecuteNonQueryCallCount);
    }

    [Fact]
    public async Task UpsertWithoutVectorPropertyReturnsKeyAsync()
    {
        // Arrange
        var expectedRecord = new TestRecordWithoutVectorProperty<ulong> { Key = 1, Data = "Test data" };

        var mockReader = new Mock<DbDataReader>();

        SetupDbDataReaderUpsertBatch(mockReader, [expectedRecord.Key]);

        using var fakeCommand = new FakeDbCommand(mockReader.Object);
        using var fakeConnection = new FakeDBConnection(fakeCommand);

        var sut = new SqliteVectorStoreRecordCollection<TestRecordWithoutVectorProperty<ulong>>(fakeConnection, "UpsertWithoutVectorProperty");

        // Act
        var actualKey = await sut.UpsertAsync(expectedRecord);

        // Assert
        Assert.Equal(expectedRecord.Key, actualKey);

        Assert.Equal(0, fakeCommand.ExecuteNonQueryCallCount);
    }

    [Fact]
    public async Task UpsertBatchReturnsKeysAsync()
    {
        // Arrange
        var expectedRecord1 = new TestRecord<ulong> { Key = 1, Data = "Test data", Vector = new ReadOnlyMemory<float>([1f, 2f, 3f, 4f]) };
        var expectedRecord2 = new TestRecord<ulong> { Key = 2, Data = "Test data", Vector = new ReadOnlyMemory<float>([1f, 2f, 3f, 4f]) };
        var expectedRecord3 = new TestRecord<ulong> { Key = 3, Data = "Test data", Vector = new ReadOnlyMemory<float>([1f, 2f, 3f, 4f]) };

        var expectedRecords = new List<TestRecord<ulong>> { expectedRecord1, expectedRecord2, expectedRecord3 };

        var mockReader = new Mock<DbDataReader>();

        SetupDbDataReaderUpsertBatch(mockReader, expectedRecords.Select(l => l.Key));

        using var fakeCommand = new FakeDbCommand(mockReader.Object);
        using var fakeConnection = new FakeDBConnection(fakeCommand);

        var sut = new SqliteVectorStoreRecordCollection<TestRecord<ulong>>(fakeConnection, "UpsertBatch");

        // Act
        var actualKeys = await sut.UpsertBatchAsync(expectedRecords).ToListAsync();

        // Assert
        Assert.Contains(expectedRecord1.Key, actualKeys);
        Assert.Contains(expectedRecord2.Key, actualKeys);
        Assert.Contains(expectedRecord3.Key, actualKeys);
    }

    [Fact]
    public async Task DeleteCallsExecuteNonQueryMethodAsync()
    {
        using var fakeCommandWithVectorProperty = new FakeDbCommand();
        using var fakeConnectionWithVectorProperty = new FakeDBConnection(fakeCommandWithVectorProperty);

        using var fakeCommandWithoutVectorProperty = new FakeDbCommand();
        using var fakeConnectionWithoutVectorProperty = new FakeDBConnection(fakeCommandWithoutVectorProperty);

        var collectionWithVectorProperty = new SqliteVectorStoreRecordCollection<TestRecord<ulong>>(fakeConnectionWithVectorProperty, "WithVectorProperty");
        var collectionWithoutVectorProperty = new SqliteVectorStoreRecordCollection<TestRecordWithoutVectorProperty<ulong>>(fakeConnectionWithoutVectorProperty, "WithoutVectorProperty");

        // Act
        await collectionWithVectorProperty.DeleteAsync(key: 1);
        await collectionWithoutVectorProperty.DeleteAsync(key: 2);

        // Assert
        Assert.Equal(2, fakeCommandWithVectorProperty.ExecuteNonQueryCallCount);
        Assert.Equal(1, fakeCommandWithoutVectorProperty.ExecuteNonQueryCallCount);
    }

    [Fact]
    public async Task DeleteBatchCallsExecuteNonQueryMethodAsync()
    {
        using var fakeCommandWithVectorProperty = new FakeDbCommand();
        using var fakeConnectionWithVectorProperty = new FakeDBConnection(fakeCommandWithVectorProperty);

        using var fakeCommandWithoutVectorProperty = new FakeDbCommand();
        using var fakeConnectionWithoutVectorProperty = new FakeDBConnection(fakeCommandWithoutVectorProperty);

        var collectionWithVectorProperty = new SqliteVectorStoreRecordCollection<TestRecord<ulong>>(fakeConnectionWithVectorProperty, "WithVectorProperty");
        var collectionWithoutVectorProperty = new SqliteVectorStoreRecordCollection<TestRecordWithoutVectorProperty<ulong>>(fakeConnectionWithoutVectorProperty, "WithoutVectorProperty");

        // Act
        await collectionWithVectorProperty.DeleteBatchAsync(keys: [1, 2, 3]);
        await collectionWithoutVectorProperty.DeleteBatchAsync(keys: [4, 5, 6]);

        // Assert
        Assert.Equal(2, fakeCommandWithVectorProperty.ExecuteNonQueryCallCount);
        Assert.Equal(1, fakeCommandWithoutVectorProperty.ExecuteNonQueryCallCount);
    }

    #region private

    private static void SetupDbDataReaderGetBatch<TKey>(Mock<DbDataReader> mockReader, List<TestRecord<TKey>> records)
    {
        var readSequence = mockReader.SetupSequence(l => l.ReadAsync(It.IsAny<CancellationToken>()));

        var numericKeySequence = mockReader.SetupSequence(l => l.GetInt64(0));
        var stringKeySequence = mockReader.SetupSequence(l => l.GetString(0));

        var dataSequence = mockReader.SetupSequence(l => l.GetString(1));
        var vectorSequence = mockReader.SetupSequence(l => l[2]);

        mockReader.Setup(l => l.IsDBNull(It.IsAny<int>())).Returns(false);

        mockReader.Setup(l => l.GetOrdinal(nameof(TestRecord<TKey>.Key))).Returns(0);
        mockReader.Setup(l => l.GetOrdinal(nameof(TestRecord<TKey>.Data))).Returns(1);
        mockReader.Setup(l => l.GetOrdinal(nameof(TestRecord<TKey>.Vector))).Returns(2);

        foreach (var record in records)
        {
            var vectorBytes = SqliteVectorStoreRecordPropertyMapping.MapVectorForStorageModel(record.Vector);

            if (record.Key is ulong numericKey)
            {
                numericKeySequence.Returns((long)numericKey);
            }

            if (record.Key is string stringKey)
            {
                stringKeySequence.Returns(stringKey);
            }

            dataSequence.Returns(record.Data!);
            vectorSequence.Returns(vectorBytes);

            readSequence.ReturnsAsync(true);
        }

        readSequence.ReturnsAsync(false);
    }

    private static void SetupDbDataReaderUpsertBatch<TKey>(Mock<DbDataReader> mockReader, IEnumerable<TKey> keys)
    {
        var readSequence = mockReader.SetupSequence(l => l.ReadAsync(It.IsAny<CancellationToken>()));
        var keySequence = mockReader.SetupSequence(l => l.GetFieldValue<TKey>(0));

        foreach (var key in keys)
        {
            keySequence.Returns(key);
            readSequence.ReturnsAsync(true);
        }

        readSequence.ReturnsAsync(false);
    }

    private static void AssertRecord<TKey>(TestRecord<TKey> expectedRecord, TestRecord<TKey>? actualRecord, bool includeVectors)
    {
        Assert.NotNull(actualRecord);

        Assert.Equal(expectedRecord.Key, actualRecord.Key);
        Assert.Equal(expectedRecord.Data, actualRecord.Data);

        if (includeVectors)
        {
            Assert.NotNull(actualRecord.Vector);
            Assert.Equal(expectedRecord.Vector!.Value.ToArray(), actualRecord.Vector.Value.Span.ToArray());
        }
        else
        {
            Assert.Null(actualRecord.Vector);
        }
    }

#pragma warning disable CA1812
    private sealed class TestRecord<TKey>
    {
        [VectorStoreRecordKey]
        public TKey? Key { get; set; }

        [VectorStoreRecordData]
        public string? Data { get; set; }

        [VectorStoreRecordVector(Dimensions: 4, DistanceFunction: DistanceFunction.CosineDistance)]
        public ReadOnlyMemory<float>? Vector { get; set; }
    }

    private sealed class TestRecordWithoutVectorProperty<TKey>
    {
        [VectorStoreRecordKey]
        public TKey? Key { get; set; }

        [VectorStoreRecordData]
        public string? Data { get; set; }
    }
#pragma warning restore CA1812

    #endregion
}

#endif

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Kusto.Cloud.Platform.Utils;
using Kusto.Data.Common;
using Microsoft.SemanticKernel.Connectors.Memory.Kusto;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Memory.Kusto;

/// <summary>
/// Unit tests for <see cref="KustoMemoryStore"/> class.
/// </summary>
public class KustoMemoryStoreTests
{
    private const string CollectionName = "fake_collection";
    private const string DatabaseName = "FakeDb";
    private readonly Mock<ICslQueryProvider> _cslQueryProviderMock;
    private readonly Mock<ICslAdminProvider> _cslAdminProviderMock;

    public KustoMemoryStoreTests()
    {
        this._cslQueryProviderMock = new Mock<ICslQueryProvider>();
        this._cslAdminProviderMock = new Mock<ICslAdminProvider>();

        this._cslAdminProviderMock
           .Setup(client => client.ExecuteControlCommandAsync(
               DatabaseName,
               It.IsAny<string>(),
               It.IsAny<ClientRequestProperties>()))
           .ReturnsAsync(FakeEmptyResult());

        this._cslAdminProviderMock
           .Setup(client => client.ExecuteControlCommand(
               DatabaseName,
               It.IsAny<string>(),
               It.IsAny<ClientRequestProperties>()))
           .Returns(FakeEmptyResult());

        this._cslQueryProviderMock
           .Setup(client => client.ExecuteQueryAsync(
               DatabaseName,
               It.IsAny<string>(),
               It.IsAny<ClientRequestProperties>(),
               It.IsAny<CancellationToken>()))
           .ReturnsAsync(FakeEmptyResult());
    }

    [Fact]
    public async Task ItCanCreateCollectionAsync()
    {
        // Arrange
        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, DatabaseName);

        // Act
        await store.CreateCollectionAsync(CollectionName);

        // Assert
        this._cslAdminProviderMock
            .Verify(client => client.ExecuteControlCommandAsync(
                DatabaseName,
                It.Is<string>(s => s.StartsWith($".create table {CollectionName}")),
                It.Is<ClientRequestProperties>(crp => string.Equals(crp.Application, Telemetry.HttpUserAgent, StringComparison.Ordinal))
            ), Times.Once());
    }

    [Fact]
    public async Task ItCanDeleteCollectionAsync()
    {
        // Arrange
        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, DatabaseName);

        // Act
        await store.DeleteCollectionAsync(CollectionName);

        // Assert
        // Assert
        this._cslAdminProviderMock
            .Verify(client => client.ExecuteControlCommandAsync(
                DatabaseName,
                It.Is<string>(s => s.StartsWith($".drop table {CollectionName}")),
                It.Is<ClientRequestProperties>(crp => string.Equals(crp.Application, Telemetry.HttpUserAgent, StringComparison.Ordinal))
            ), Times.Once());
    }

    [Fact]
    public async Task ItReturnsTrueWhenCollectionExistsAsync()
    {
        // Arrange
        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, DatabaseName);

        this._cslAdminProviderMock
            .Setup(client => client.ExecuteControlCommandAsync(
                DatabaseName,
                It.Is<string>(s => s.StartsWith(CslCommandGenerator.GenerateTablesShowCommand())),
                It.IsAny<ClientRequestProperties>()))
            .ReturnsAsync(CollectionToSingleColumnDataReader(new[] { CollectionName }));

        // Act
        var doesCollectionExist = await store.DoesCollectionExistAsync(CollectionName);

        // Assert
        Assert.True(doesCollectionExist);
    }

    [Fact]
    public async Task ItReturnsFalseWhenCollectionDoesNotExistAsync()
    {
        // Arrange
        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, DatabaseName);

        this._cslAdminProviderMock
            .Setup(client => client.ExecuteControlCommandAsync(
                DatabaseName,
                It.Is<string>(s => s.StartsWith(CslCommandGenerator.GenerateTablesShowCommand())),
                It.IsAny<ClientRequestProperties>()))
            .ReturnsAsync(FakeEmptyResult());

        // Act
        var doesCollectionExist = await store.DoesCollectionExistAsync(CollectionName);

        // Assert
        Assert.False(doesCollectionExist);
    }

    [Fact]
    public async Task ItCanUpsertAsync()
    {
        // Arrange
        var expectedMemoryRecord = this.GetRandomMemoryRecord();
        var kustoMemoryEntry = new KustoMemoryRecord(expectedMemoryRecord);

        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, DatabaseName);

        // Act
        var actualMemoryRecordKey = await store.UpsertAsync(CollectionName, expectedMemoryRecord);

        // Assert
        this._cslAdminProviderMock.Verify(client => client.ExecuteControlCommandAsync(
            DatabaseName,
            It.Is<string>(s => s.StartsWith($".ingest inline into table {CollectionName}", StringComparison.Ordinal) && s.Contains(actualMemoryRecordKey, StringComparison.Ordinal)),
            It.IsAny<ClientRequestProperties>()), Times.Once());
        Assert.Equal(expectedMemoryRecord.Key, actualMemoryRecordKey);
    }

    [Fact]
    public async Task ItCanUpsertBatchAsyncAsync()
    {
        // Arrange
        var memoryRecord1 = this.GetRandomMemoryRecord();
        var memoryRecord2 = this.GetRandomMemoryRecord();
        var memoryRecord3 = this.GetRandomMemoryRecord();

        var batchUpsertMemoryRecords = new[] { memoryRecord1, memoryRecord2, memoryRecord3 };
        var expectedMemoryRecordKeys = batchUpsertMemoryRecords.Select(l => l.Key).ToList();

        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, DatabaseName);

        // Act
        var actualMemoryRecordKeys = await store.UpsertBatchAsync(CollectionName, batchUpsertMemoryRecords).ToListAsync();

        // Assert
        this._cslAdminProviderMock
            .Verify(client => client.ExecuteControlCommandAsync(
                DatabaseName,
                It.Is<string>(s =>
                    s.StartsWith($".ingest inline into table {CollectionName}", StringComparison.Ordinal) &&
                    batchUpsertMemoryRecords.All(r => s.Contains(r.Key, StringComparison.Ordinal))),
                It.IsAny<ClientRequestProperties>()
            ), Times.Once());

        for (int i = 0; i < expectedMemoryRecordKeys.Count; i++)
        {
            Assert.Equal(expectedMemoryRecordKeys[i], actualMemoryRecordKeys[i]);
        }
    }

    [Fact]
    public async Task ItCanGetMemoryRecordFromCollectionAsync()
    {
        // Arrange
        var expectedMemoryRecord = this.GetRandomMemoryRecord();
        var kustoMemoryEntry = new KustoMemoryRecord(expectedMemoryRecord);

        this._cslQueryProviderMock
            .Setup(client => client.ExecuteQueryAsync(
                DatabaseName,
                It.Is<string>(s => s.Contains(CollectionName) && s.Contains(expectedMemoryRecord.Key)),
                It.IsAny<ClientRequestProperties>(),
                CancellationToken.None))
            .ReturnsAsync(CollectionToDataReader(new string[][] {
                new string[] {
                    expectedMemoryRecord.Key,
                    KustoSerializer.SerializeMetadata(expectedMemoryRecord.Metadata),
                    KustoSerializer.SerializeDateTimeOffset(expectedMemoryRecord.Timestamp),
                    KustoSerializer.SerializeEmbedding(expectedMemoryRecord.Embedding),
                }}));

        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, DatabaseName);

        // Act
        var actualMemoryRecord = await store.GetAsync(CollectionName, expectedMemoryRecord.Key, withEmbedding: true);

        // Assert
        Assert.NotNull(actualMemoryRecord);
        this.AssertMemoryRecordEqual(expectedMemoryRecord, actualMemoryRecord);
    }

    [Fact]
    public async Task ItReturnsNullWhenMemoryRecordDoesNotExistAsync()
    {
        // Arrange
        const string memoryRecordKey = "fake-record-key";

        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, DatabaseName);

        // Act
        var actualMemoryRecord = await store.GetAsync(CollectionName, memoryRecordKey, withEmbedding: true);

        // Assert
        Assert.Null(actualMemoryRecord);
    }

    [Fact]
    public async Task ItCanGetMemoryRecordBatchFromCollectionAsync()
    {
        // Arrange
        var memoryRecord1 = this.GetRandomMemoryRecord();
        var memoryRecord2 = this.GetRandomMemoryRecord();
        var memoryRecord3 = this.GetRandomMemoryRecord();

        var batchUpsertMemoryRecords = new[] { memoryRecord1, memoryRecord2, memoryRecord3 };
        var expectedMemoryRecordKeys = batchUpsertMemoryRecords.Select(l => l.Key).ToList();

        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, DatabaseName);
        this._cslQueryProviderMock
            .Setup(client => client.ExecuteQueryAsync(
                DatabaseName,
                It.Is<string>(s =>
                    s.Contains(CollectionName, StringComparison.Ordinal) &&
                    batchUpsertMemoryRecords.All(r => s.Contains(r.Key, StringComparison.Ordinal))),
                It.IsAny<ClientRequestProperties>(),
                CancellationToken.None))
            .ReturnsAsync(CollectionToDataReader(batchUpsertMemoryRecords.Select(r => new string[] {
                    r.Key,
                    KustoSerializer.SerializeMetadata(r.Metadata),
                    KustoSerializer.SerializeDateTimeOffset(r.Timestamp),
                    KustoSerializer.SerializeEmbedding(r.Embedding),
                }).ToArray()));

        // Act
        var actualMemoryRecords = await store.GetBatchAsync(CollectionName, expectedMemoryRecordKeys, withEmbeddings: true).ToListAsync();

        // Assert
        Assert.NotNull(actualMemoryRecords);
        for (var i = 0; i < actualMemoryRecords.Count; i++)
        {
            this.AssertMemoryRecordEqual(batchUpsertMemoryRecords[i], actualMemoryRecords[i]);
        }
    }

    [Fact]
    public async Task ItCanReturnCollectionsAsync()
    {
        // Arrange
        var expectedCollections = new List<string> { "fake-collection-1", "fake-collection-2", "fake-collection-3" };

        this._cslAdminProviderMock
            .Setup(client => client.ExecuteControlCommandAsync(
                DatabaseName,
                It.Is<string>(s => s.StartsWith(CslCommandGenerator.GenerateTablesShowCommand(), StringComparison.Ordinal)),
                It.IsAny<ClientRequestProperties>())
            ).ReturnsAsync(CollectionToSingleColumnDataReader(expectedCollections));

        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, DatabaseName);

        // Act
        var actualCollections = await store.GetCollectionsAsync().ToListAsync();

        // Assert
        Assert.Equal(expectedCollections.Count, actualCollections.Count);

        for (var i = 0; i < expectedCollections.Count; i++)
        {
            Assert.Equal(expectedCollections[i], actualCollections[i]);
        }
    }

    [Fact]
    public async Task ItCanRemoveAsync()
    {
        // Arrange
        const string memoryRecordKey = "fake-record-key";
        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, DatabaseName);

        // Act
        await store.RemoveAsync(CollectionName, memoryRecordKey);

        // Assert
        this._cslAdminProviderMock
            .Verify(client => client.ExecuteControlCommandAsync(
                DatabaseName,
                It.Is<string>(s => s.Replace("  ", " ").StartsWith($".delete table {CollectionName}") && s.Contains(memoryRecordKey)), // Replace double spaces with single space to account for the fact that the query is formatted with double spaces and to be future proof
                It.IsAny<ClientRequestProperties>()
            ), Times.Once());
    }

    [Fact]
    public async Task ItCanRemoveBatchAsync()
    {
        // Arrange
        string[] memoryRecordKeys = new string[] { "fake-record-key1", "fake-record-key2", "fake-record-key3" };
        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, DatabaseName);

        // Act
        await store.RemoveBatchAsync(CollectionName, memoryRecordKeys);

        // Assert
        this._cslAdminProviderMock
            .Verify(client => client.ExecuteControlCommandAsync(
                DatabaseName,
                It.Is<string>(s => s.Replace("  ", " ").StartsWith($".delete table {CollectionName}") && memoryRecordKeys.All(r => s.Contains(r, StringComparison.OrdinalIgnoreCase))),
                It.IsAny<ClientRequestProperties>()
            ), Times.Once());
    }

    #region private ================================================================================

    private void AssertMemoryRecordEqual(MemoryRecord expectedRecord, MemoryRecord actualRecord)
    {
        Assert.Equal(expectedRecord.Key, actualRecord.Key);
        Assert.Equal(expectedRecord.Timestamp, actualRecord.Timestamp);
        Assert.True(expectedRecord.Embedding.Span.SequenceEqual(actualRecord.Embedding.Span));
        Assert.Equal(expectedRecord.Metadata.Id, actualRecord.Metadata.Id);
        Assert.Equal(expectedRecord.Metadata.Text, actualRecord.Metadata.Text);
        Assert.Equal(expectedRecord.Metadata.Description, actualRecord.Metadata.Description);
        Assert.Equal(expectedRecord.Metadata.AdditionalMetadata, actualRecord.Metadata.AdditionalMetadata);
        Assert.Equal(expectedRecord.Metadata.IsReference, actualRecord.Metadata.IsReference);
        Assert.Equal(expectedRecord.Metadata.ExternalSourceName, actualRecord.Metadata.ExternalSourceName);
    }

    private MemoryRecord GetRandomMemoryRecord(ReadOnlyMemory<float>? embedding = null)
    {
        var id = Guid.NewGuid().ToString();
        var memoryEmbedding = embedding ?? new[] { 1f, 3f, 5f };

        return MemoryRecord.LocalRecord(
            id: id,
            text: "text-" + Guid.NewGuid().ToString(),
            description: "description-" + Guid.NewGuid().ToString(),
            embedding: memoryEmbedding,
            additionalMetadata: "metadata-" + Guid.NewGuid().ToString(),
            key: id,
            timestamp: new DateTimeOffset(2023, 8, 4, 23, 59, 59, TimeSpan.Zero));
    }

    private static DataTableReader FakeEmptyResult() => Array.Empty<string[]>().ToDataTable().CreateDataReader();

    private static DataTableReader CollectionToSingleColumnDataReader(IEnumerable<string> collection)
    {
        using var table = new DataTable();
        table.Columns.Add("Column1", typeof(string));

        foreach (var item in collection)
        {
            table.Rows.Add(item);
        }

        return table.CreateDataReader();
    }

    private static DataTableReader CollectionToDataReader(string[][] data)
    {
        using var table = new DataTable();

        if (data != null)
        {
            data = data.ToArrayIfNotAlready();
            if (data[0] != null)
            {
                for (int i = 0; i < data[0].Length; i++)
                {
                    table.Columns.Add($"Column{i + 1}", typeof(string));
                }
            }

            for (int i = 0; i < data.Length; i++)
            {
                table.Rows.Add(data[i]);
            }
        }

        return table.CreateDataReader();
    }

    #endregion
}

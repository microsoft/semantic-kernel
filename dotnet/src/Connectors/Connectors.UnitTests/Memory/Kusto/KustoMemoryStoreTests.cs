// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Data;
using System.Globalization;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Kusto.Cloud.Platform.Utils;
using Kusto.Data.Common;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Connectors.Memory.Kusto;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Moq;
using Newtonsoft.Json;
using NRedisStack.Graph;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Memory.Kusto;

/// <summary>
/// Unit tests for <see cref="KustoMemoryStore"/> class.
/// </summary>
public class KustoMemoryStoreTests
{
    private const string c_collectionName = "fake_collection";
    private const string c_databaseName = "FakeDb";
    private readonly Mock<ICslQueryProvider> _cslQueryProviderMock;
    private readonly Mock<ICslAdminProvider> _cslAdminProviderMock;

    public KustoMemoryStoreTests()
    {
        this._cslQueryProviderMock = new Mock<ICslQueryProvider>();
        this._cslAdminProviderMock = new Mock<ICslAdminProvider>();

        this._cslAdminProviderMock
           .Setup(client => client.ExecuteControlCommandAsync(
               c_databaseName,
               It.IsAny<string>(),
               It.IsAny<ClientRequestProperties>()))
           .ReturnsAsync(FakeEmptyResult());

        this._cslAdminProviderMock
           .Setup(client => client.ExecuteControlCommand(
               c_databaseName,
               It.IsAny<string>(),
               It.IsAny<ClientRequestProperties>()))
           .Returns(FakeEmptyResult());

        this._cslQueryProviderMock
           .Setup(client => client.ExecuteQueryAsync(
               c_databaseName,
               It.IsAny<string>(),
               It.IsAny<ClientRequestProperties>(),
               It.IsAny<CancellationToken>()))
           .ReturnsAsync(FakeEmptyResult());
    }

    [Fact]
    public async Task ItCanCreateCollectionAsync()
    {
        // Arrange
        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, c_databaseName);

        // Act
        await store.CreateCollectionAsync(c_collectionName);

        // Assert
        this._cslAdminProviderMock
            .Verify(client => client.ExecuteControlCommandAsync(
                c_databaseName,
                It.Is<string>(s => s.StartsWith($".create table {c_collectionName}")),
                It.Is<ClientRequestProperties>(crp => string.Equals(crp.Application, Telemetry.HttpUserAgent, StringComparison.Ordinal))
            ), Times.Once());
    }

    [Fact]
    public async Task ItCanDeleteCollectionAsync()
    {
        // Arrange
        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, c_databaseName);

        // Act
        await store.DeleteCollectionAsync(c_collectionName);

        // Assert
        // Assert
        this._cslAdminProviderMock
            .Verify(client => client.ExecuteControlCommandAsync(
                c_databaseName,
                It.Is<string>(s => s.StartsWith($".drop table {c_collectionName}")),
                It.Is<ClientRequestProperties>(crp => string.Equals(crp.Application, Telemetry.HttpUserAgent, StringComparison.Ordinal))
            ), Times.Once());
    }

    [Fact]
    public async Task ItReturnsTrueWhenCollectionExistsAsync()
    {
        // Arrange
        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, c_databaseName);

        this._cslAdminProviderMock
            .Setup(client => client.ExecuteControlCommandAsync(
                c_databaseName,
                It.Is<string>(s => s.StartsWith(CslCommandGenerator.GenerateTablesShowCommand())),
                It.IsAny<ClientRequestProperties>()))
            .ReturnsAsync(CollectionToSingleColumnDataReader(new[] { c_collectionName }));

        // Act
        var doesCollectionExist = await store.DoesCollectionExistAsync(c_collectionName);

        // Assert
        Assert.True(doesCollectionExist);
    }

    [Fact]
    public async Task ItReturnsFalseWhenCollectionDoesNotExistAsync()
    {
        // Arrange
        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, c_databaseName);

        this._cslAdminProviderMock
            .Setup(client => client.ExecuteControlCommandAsync(
                c_databaseName,
                It.Is<string>(s => s.StartsWith(CslCommandGenerator.GenerateTablesShowCommand())),
                It.IsAny<ClientRequestProperties>()))
            .ReturnsAsync(FakeEmptyResult());

        // Act
        var doesCollectionExist = await store.DoesCollectionExistAsync(c_collectionName);

        // Assert
        Assert.False(doesCollectionExist);
    }

    [Fact]
    public async Task ItCanUpsertAsync()
    {
        // Arrange
        var expectedMemoryRecord = this.GetRandomMemoryRecord();
        var kustoMemoryEntry = new KustoMemoryRecord(expectedMemoryRecord);

        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, c_databaseName);

        // Act
        var actualMemoryRecordKey = await store.UpsertAsync(c_collectionName, expectedMemoryRecord);

        // Assert
        this._cslAdminProviderMock.Verify(client => client.ExecuteControlCommandAsync(
            c_databaseName,
            It.Is<string>(s => s.StartsWith($".ingest inline into table {c_collectionName}", StringComparison.Ordinal) && s.Contains(actualMemoryRecordKey, StringComparison.Ordinal)),
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

        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, c_databaseName);

        // Act
        var actualMemoryRecordKeys = await store.UpsertBatchAsync(c_collectionName, batchUpsertMemoryRecords).ToListAsync();

        // Assert
        this._cslAdminProviderMock
            .Verify(client => client.ExecuteControlCommandAsync(
                c_databaseName,
                It.Is<string>(s =>
                    s.StartsWith($".ingest inline into table {c_collectionName}", StringComparison.Ordinal) &&
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
                c_databaseName,
                It.Is<string>(s => s.Contains(c_collectionName) && s.Contains(expectedMemoryRecord.Key)),
                It.IsAny<ClientRequestProperties>(),
                CancellationToken.None))
            .ReturnsAsync(CollectionToDataReader(new string[][] {
                new string[] {
                    expectedMemoryRecord.Key,
                    KustoSerializer.SerializeMetadata(expectedMemoryRecord.Metadata),
                    KustoSerializer.SerializeDateTimeOffset(expectedMemoryRecord.Timestamp),
                    KustoSerializer.SerializeEmbedding(expectedMemoryRecord.Embedding),
                }}));

        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, c_databaseName);

        // Act
        var actualMemoryRecord = await store.GetAsync(c_collectionName, expectedMemoryRecord.Key, withEmbedding: true);

        // Assert
        Assert.NotNull(actualMemoryRecord);
        this.AssertMemoryRecordEqual(expectedMemoryRecord, actualMemoryRecord);
    }

    [Fact]
    public async Task ItReturnsNullWhenMemoryRecordDoesNotExistAsync()
    {
        // Arrange
        const string memoryRecordKey = "fake-record-key";

        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, c_databaseName);

        // Act
        var actualMemoryRecord = await store.GetAsync(c_collectionName, memoryRecordKey, withEmbedding: true);

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

        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, c_databaseName);
        this._cslQueryProviderMock
            .Setup(client => client.ExecuteQueryAsync(
                c_databaseName,
                It.Is<string>(s =>
                    s.Contains(c_collectionName, StringComparison.Ordinal) &&
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
        var actualMemoryRecords = await store.GetBatchAsync(c_collectionName, expectedMemoryRecordKeys, withEmbeddings: true).ToListAsync();

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
                c_databaseName,
                It.Is<string>(s => s.StartsWith(CslCommandGenerator.GenerateTablesShowCommand(), StringComparison.Ordinal)),
                It.IsAny<ClientRequestProperties>())
            ).ReturnsAsync(CollectionToSingleColumnDataReader(expectedCollections));

        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, c_databaseName);

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
        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, c_databaseName);

        // Act
        await store.RemoveAsync(c_collectionName, memoryRecordKey);

        // Assert
        this._cslAdminProviderMock
            .Verify(client => client.ExecuteControlCommandAsync(
                c_databaseName,
                It.Is<string>(s => s.Replace("  ", " ").StartsWith($".delete table {c_collectionName}") && s.Contains(memoryRecordKey)), // Replace double spaces with single space to account for the fact that the query is formatted with double spaces and to be future proof
                It.IsAny<ClientRequestProperties>()
            ), Times.Once());
    }

    [Fact]
    public async Task ItCanRemoveBatchAsync()
    {
        // Arrange
        string[] memoryRecordKeys = new string[] { "fake-record-key1", "fake-record-key2", "fake-record-key3" };
        using var store = new KustoMemoryStore(this._cslAdminProviderMock.Object, this._cslQueryProviderMock.Object, c_databaseName);

        // Act
        await store.RemoveBatchAsync(c_collectionName, memoryRecordKeys);

        // Assert
        this._cslAdminProviderMock
            .Verify(client => client.ExecuteControlCommandAsync(
                c_databaseName,
                It.Is<string>(s => s.Replace("  ", " ").StartsWith($".delete table {c_collectionName}") && memoryRecordKeys.All(r => s.Contains(r, StringComparison.OrdinalIgnoreCase))),
                It.IsAny<ClientRequestProperties>()
            ), Times.Once());
    }

    #region private ================================================================================

    private void AssertMemoryRecordEqual(MemoryRecord expectedRecord, MemoryRecord actualRecord)
    {
        Assert.Equal(expectedRecord.Key, actualRecord.Key);
        Assert.Equal(expectedRecord.Embedding.Vector, actualRecord.Embedding.Vector);
        Assert.Equal(expectedRecord.Metadata.Id, actualRecord.Metadata.Id);
        Assert.Equal(expectedRecord.Metadata.Text, actualRecord.Metadata.Text);
        Assert.Equal(expectedRecord.Metadata.Description, actualRecord.Metadata.Description);
        Assert.Equal(expectedRecord.Metadata.AdditionalMetadata, actualRecord.Metadata.AdditionalMetadata);
        Assert.Equal(expectedRecord.Metadata.IsReference, actualRecord.Metadata.IsReference);
        Assert.Equal(expectedRecord.Metadata.ExternalSourceName, actualRecord.Metadata.ExternalSourceName);
    }

    private MemoryRecord GetRandomMemoryRecord(Embedding<float>? embedding = null)
    {
        var id = Guid.NewGuid().ToString();
        var memoryEmbedding = embedding ?? new Embedding<float>(new[] { 1f, 3f, 5f });

        return MemoryRecord.LocalRecord(
            id: id,
            text: "text-" + Guid.NewGuid().ToString(),
            description: "description-" + Guid.NewGuid().ToString(),
            embedding: memoryEmbedding,
            additionalMetadata: "metadata-" + Guid.NewGuid().ToString(),
            key: id,
            timestamp: DateTimeOffset.Now);
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

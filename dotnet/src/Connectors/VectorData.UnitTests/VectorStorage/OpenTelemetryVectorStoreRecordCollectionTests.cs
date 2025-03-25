// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Moq;
using OpenTelemetry.Trace;
using Xunit;

namespace VectorData.UnitTests.VectorStorage;

public class OpenTelemetryVectorStoreRecordCollectionTests
{
    private readonly Mock<IVectorStoreRecordCollection<string, object>> _mockCollection;

    public OpenTelemetryVectorStoreRecordCollectionTests()
    {
        this._mockCollection = new();

        this._mockCollection.Setup(c => c.GetService(typeof(VectorStoreRecordCollectionMetadata), It.IsAny<object?>()))
            .Returns(new VectorStoreRecordCollectionMetadata
            {
                VectorStoreSystemName = "testvectorstore",
                DatabaseName = "testdb",
                CollectionName = "testcollection"
            });
    }

    [Fact]
    public async Task CollectionExistsWorksWithActivityAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();

        this._mockCollection.Setup(c => c.CollectionExistsAsync(default)).ReturnsAsync(true);

        var innerCollection = this._mockCollection.Object;
        var vectorStoreCollection = innerCollection
            .AsBuilder()
            .UseOpenTelemetry(sourceName)
            .Build();

        var activities = new List<Activity>();
        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        // Act
        var result = await vectorStoreCollection.CollectionExistsAsync();

        // Assert
        Assert.True(result);

        var activity = Assert.Single(activities);

        Assert.Equal("collection_exists testcollection", activity.DisplayName);
        Assert.Equal("collection_exists", activity.GetTagItem("db.operation.name"));
        Assert.Equal("testdb", activity.GetTagItem("db.namespace"));
        Assert.Equal("testcollection", activity.GetTagItem("db.collection.name"));
        Assert.Equal("testvectorstore", activity.GetTagItem("db.system.name"));
    }

    [Fact]
    public async Task CreateCollectionWorksWithActivityAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();

        this._mockCollection.Setup(c => c.CreateCollectionAsync(default)).Returns(Task.CompletedTask);

        var innerCollection = this._mockCollection.Object;
        var vectorStoreCollection = innerCollection
            .AsBuilder()
            .UseOpenTelemetry(sourceName)
            .Build();

        var activities = new List<Activity>();
        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        // Act
        await vectorStoreCollection.CreateCollectionAsync();

        // Assert
        var activity = Assert.Single(activities);

        Assert.Equal("create_collection testcollection", activity.DisplayName);
        Assert.Equal("create_collection", activity.GetTagItem("db.operation.name"));
        Assert.Equal("testdb", activity.GetTagItem("db.namespace"));
        Assert.Equal("testcollection", activity.GetTagItem("db.collection.name"));
        Assert.Equal("testvectorstore", activity.GetTagItem("db.system.name"));
    }

    [Fact]
    public async Task CreateCollectionIfNotExistsWorksWithActivityAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();

        this._mockCollection.Setup(c => c.CreateCollectionIfNotExistsAsync(default)).Returns(Task.CompletedTask);

        var innerCollection = this._mockCollection.Object;
        var vectorStoreCollection = innerCollection
            .AsBuilder()
            .UseOpenTelemetry(sourceName)
            .Build();

        var activities = new List<Activity>();
        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        // Act
        await vectorStoreCollection.CreateCollectionIfNotExistsAsync();

        // Assert
        var activity = Assert.Single(activities);

        Assert.Equal("create_collection_if_not_exists testcollection", activity.DisplayName);
        Assert.Equal("create_collection_if_not_exists", activity.GetTagItem("db.operation.name"));
        Assert.Equal("testdb", activity.GetTagItem("db.namespace"));
        Assert.Equal("testcollection", activity.GetTagItem("db.collection.name"));
        Assert.Equal("testvectorstore", activity.GetTagItem("db.system.name"));
    }

    [Fact]
    public async Task DeleteCollectionWorksWithActivityAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();

        this._mockCollection.Setup(c => c.DeleteCollectionAsync(default)).Returns(Task.CompletedTask);

        var innerCollection = this._mockCollection.Object;
        var vectorStoreCollection = innerCollection
            .AsBuilder()
            .UseOpenTelemetry(sourceName)
            .Build();

        var activities = new List<Activity>();
        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        // Act
        await vectorStoreCollection.DeleteCollectionAsync();

        // Assert
        var activity = Assert.Single(activities);

        Assert.Equal("delete_collection testcollection", activity.DisplayName);
        Assert.Equal("delete_collection", activity.GetTagItem("db.operation.name"));
        Assert.Equal("testdb", activity.GetTagItem("db.namespace"));
        Assert.Equal("testcollection", activity.GetTagItem("db.collection.name"));
        Assert.Equal("testvectorstore", activity.GetTagItem("db.system.name"));
    }

    [Fact]
    public async Task GetWorksWithActivityAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();
        var expectedRecord = new object();

        this._mockCollection.Setup(c => c.GetAsync("key1", null, default)).ReturnsAsync(expectedRecord);

        var innerCollection = this._mockCollection.Object;
        var vectorStoreCollection = innerCollection
            .AsBuilder()
            .UseOpenTelemetry(sourceName)
            .Build();

        var activities = new List<Activity>();
        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        // Act
        var result = await vectorStoreCollection.GetAsync("key1");

        // Assert
        Assert.Equal(expectedRecord, result);

        var activity = Assert.Single(activities);

        Assert.Equal("get testcollection", activity.DisplayName);
        Assert.Equal("get", activity.GetTagItem("db.operation.name"));
        Assert.Equal("testdb", activity.GetTagItem("db.namespace"));
        Assert.Equal("testcollection", activity.GetTagItem("db.collection.name"));
        Assert.Equal("testvectorstore", activity.GetTagItem("db.system.name"));
    }

    [Fact]
    public async Task GetBatchWorksWithActivityAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();
        object[] expectedRecords = [new(), new()];
        string[] keys = ["key1", "key2"];

        this._mockCollection.Setup(c => c.GetBatchAsync(keys, null, default))
            .Returns(expectedRecords.ToAsyncEnumerable());

        var innerCollection = this._mockCollection.Object;
        var vectorStoreCollection = innerCollection
            .AsBuilder()
            .UseOpenTelemetry(sourceName)
            .Build();

        var activities = new List<Activity>();
        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        // Act
        var result = await vectorStoreCollection.GetBatchAsync(keys).ToListAsync();

        // Assert
        Assert.Equal(expectedRecords, result);

        var activity = Assert.Single(activities);

        Assert.Equal("get_batch testcollection", activity.DisplayName);
        Assert.Equal("get_batch", activity.GetTagItem("db.operation.name"));
        Assert.Equal("testdb", activity.GetTagItem("db.namespace"));
        Assert.Equal("testcollection", activity.GetTagItem("db.collection.name"));
        Assert.Equal("testvectorstore", activity.GetTagItem("db.system.name"));
    }

    [Fact]
    public async Task DeleteWorksWithActivityAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();

        this._mockCollection.Setup(c => c.DeleteAsync("key1", default)).Returns(Task.CompletedTask);

        var innerCollection = this._mockCollection.Object;
        var vectorStoreCollection = innerCollection
            .AsBuilder()
            .UseOpenTelemetry(sourceName)
            .Build();

        var activities = new List<Activity>();
        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        // Act
        await vectorStoreCollection.DeleteAsync("key1");

        // Assert
        var activity = Assert.Single(activities);

        Assert.Equal("delete testcollection", activity.DisplayName);
        Assert.Equal("delete", activity.GetTagItem("db.operation.name"));
        Assert.Equal("testdb", activity.GetTagItem("db.namespace"));
        Assert.Equal("testcollection", activity.GetTagItem("db.collection.name"));
        Assert.Equal("testvectorstore", activity.GetTagItem("db.system.name"));
    }

    [Fact]
    public async Task DeleteBatchWorksWithActivityAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();
        string[] keys = ["key1", "key2"];

        this._mockCollection.Setup(c => c.DeleteBatchAsync(keys, default)).Returns(Task.CompletedTask);

        var innerCollection = this._mockCollection.Object;
        var vectorStoreCollection = innerCollection
            .AsBuilder()
            .UseOpenTelemetry(sourceName)
            .Build();

        var activities = new List<Activity>();
        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        // Act
        await vectorStoreCollection.DeleteBatchAsync(keys);

        // Assert
        var activity = Assert.Single(activities);

        Assert.Equal("delete_batch testcollection", activity.DisplayName);
        Assert.Equal("delete_batch", activity.GetTagItem("db.operation.name"));
        Assert.Equal("testdb", activity.GetTagItem("db.namespace"));
        Assert.Equal("testcollection", activity.GetTagItem("db.collection.name"));
        Assert.Equal("testvectorstore", activity.GetTagItem("db.system.name"));
    }

    [Fact]
    public async Task UpsertWorksWithActivityAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();
        var expectedKey = "key1";

        this._mockCollection.Setup(c => c.UpsertAsync(It.IsAny<object>(), default)).ReturnsAsync(expectedKey);

        var innerCollection = this._mockCollection.Object;
        var vectorStoreCollection = innerCollection
            .AsBuilder()
            .UseOpenTelemetry(sourceName)
            .Build();

        var activities = new List<Activity>();
        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        // Act
        var result = await vectorStoreCollection.UpsertAsync(new object());

        // Assert
        Assert.Equal(expectedKey, result);

        var activity = Assert.Single(activities);

        Assert.Equal("upsert testcollection", activity.DisplayName);
        Assert.Equal("upsert", activity.GetTagItem("db.operation.name"));
        Assert.Equal("testdb", activity.GetTagItem("db.namespace"));
        Assert.Equal("testcollection", activity.GetTagItem("db.collection.name"));
        Assert.Equal("testvectorstore", activity.GetTagItem("db.system.name"));
    }

    [Fact]
    public async Task UpsertBatchWorksWithActivityAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();
        string[] expectedKeys = ["key1", "key2"];

        this._mockCollection.Setup(c => c.UpsertBatchAsync(It.IsAny<IEnumerable<object>>(), default))
            .Returns(expectedKeys.ToAsyncEnumerable());

        var innerCollection = this._mockCollection.Object;
        var vectorStoreCollection = innerCollection
            .AsBuilder()
            .UseOpenTelemetry(sourceName)
            .Build();

        var activities = new List<Activity>();
        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        // Act
        var result = await vectorStoreCollection.UpsertBatchAsync([new object(), new object()]).ToListAsync();

        // Assert
        Assert.Equal(expectedKeys, result);

        var activity = Assert.Single(activities);

        Assert.Equal("upsert_batch testcollection", activity.DisplayName);
        Assert.Equal("upsert_batch", activity.GetTagItem("db.operation.name"));
        Assert.Equal("testdb", activity.GetTagItem("db.namespace"));
        Assert.Equal("testcollection", activity.GetTagItem("db.collection.name"));
        Assert.Equal("testvectorstore", activity.GetTagItem("db.system.name"));
    }

    [Fact]
    public async Task VectorizedSearchAsyncWorksWithActivityAsync()
    {
        // Arrange
        var sourceName = Guid.NewGuid().ToString();
        var expectedResults = new VectorSearchResults<object>(new List<VectorSearchResult<object>>().ToAsyncEnumerable());

        this._mockCollection.Setup(c => c.VectorizedSearchAsync(It.IsAny<float[]>(), null, default))
            .ReturnsAsync(expectedResults);

        var innerCollection = this._mockCollection.Object;
        var vectorStoreCollection = innerCollection
            .AsBuilder()
            .UseOpenTelemetry(sourceName)
            .Build();

        var activities = new List<Activity>();
        using var tracerProvider = OpenTelemetry.Sdk.CreateTracerProviderBuilder()
            .AddSource(sourceName)
            .AddInMemoryExporter(activities)
            .Build();

        var vector = new float[] { 1.0f };

        // Act
        var result = await vectorStoreCollection.VectorizedSearchAsync(vector);

        // Assert
        Assert.Equal(expectedResults, result);

        var activity = Assert.Single(activities);

        Assert.Equal("vectorized_search testcollection", activity.DisplayName);
        Assert.Equal("vectorized_search", activity.GetTagItem("db.operation.name"));
        Assert.Equal("testdb", activity.GetTagItem("db.namespace"));
        Assert.Equal("testcollection", activity.GetTagItem("db.collection.name"));
        Assert.Equal("testvectorstore", activity.GetTagItem("db.system.name"));
    }
}

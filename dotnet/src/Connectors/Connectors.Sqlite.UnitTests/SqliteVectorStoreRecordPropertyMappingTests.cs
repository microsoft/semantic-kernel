﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Xunit;

namespace SemanticKernel.Connectors.Sqlite.UnitTests;

/// <summary>
/// Unit tests for <see cref="SqliteVectorStoreRecordPropertyMapping"/> class.
/// </summary>
public sealed class SqliteVectorStoreRecordPropertyMappingTests
{
    [Fact]
    public void MapVectorForStorageModelWithInvalidVectorTypeThrowsException()
    {
        // Arrange
        var vector = new float[] { 1f, 2f, 3f };

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => SqliteVectorStoreRecordPropertyMapping.MapVectorForStorageModel(vector));
    }

    [Fact]
    public void MapVectorForStorageModelReturnsByteArray()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1.1f, 2.2f, 3.3f, 4.4f]);

        // Act
        var storageModelVector = SqliteVectorStoreRecordPropertyMapping.MapVectorForStorageModel(vector);

        // Assert
        Assert.IsType<byte[]>(storageModelVector);
        Assert.True(storageModelVector.Length > 0);
    }

    [Fact]
    public void MapVectorForDataModelReturnsReadOnlyMemory()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1.1f, 2.2f, 3.3f, 4.4f]);
        var byteArray = SqliteVectorStoreRecordPropertyMapping.MapVectorForStorageModel(vector);

        // Act
        var dataModelVector = SqliteVectorStoreRecordPropertyMapping.MapVectorForDataModel(byteArray);

        // Assert
        Assert.Equal(vector.Span.ToArray(), dataModelVector.Span.ToArray());
    }

    [Fact]
    public void GetColumnsReturnsCollectionOfColumns()
    {
        // Arrange
        var properties = new List<VectorStoreRecordProperty>()
        {
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("Data", typeof(int)),
            new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>)) { Dimensions = 4, DistanceFunction = DistanceFunction.ManhattanDistance },
        };

        var storagePropertyNames = new Dictionary<string, string>
        {
            ["Key"] = "Key",
            ["Data"] = "my_data",
            ["Vector"] = "Vector"
        };

        // Act
        var columns = SqliteVectorStoreRecordPropertyMapping.GetColumns(properties, storagePropertyNames);

        // Assert
        Assert.Equal("Key", columns[0].Name);
        Assert.Equal("TEXT", columns[0].Type);
        Assert.True(columns[0].IsPrimary);
        Assert.Null(columns[0].Configuration);

        Assert.Equal("my_data", columns[1].Name);
        Assert.Equal("INTEGER", columns[1].Type);
        Assert.False(columns[1].IsPrimary);
        Assert.Null(columns[1].Configuration);

        Assert.Equal("Vector", columns[2].Name);
        Assert.Equal("FLOAT[4]", columns[2].Type);
        Assert.False(columns[2].IsPrimary);
        Assert.NotNull(columns[2].Configuration);

        Assert.Equal("l1", columns[2].Configuration!["distance_metric"]);
    }
}

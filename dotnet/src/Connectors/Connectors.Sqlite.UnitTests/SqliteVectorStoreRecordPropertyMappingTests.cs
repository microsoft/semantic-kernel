// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
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

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void GetColumnsReturnsCollectionOfColumns(bool data)
    {
        // Arrange
        var properties = new List<VectorStoreRecordPropertyModel>()
        {
            new VectorStoreRecordKeyPropertyModel("Key", typeof(string)) { StorageName = "Key" },
            new VectorStoreRecordDataPropertyModel("Data", typeof(int)) { StorageName = "my_data", IsIndexed = true },
            new VectorStoreRecordVectorPropertyModel("Vector", typeof(ReadOnlyMemory<float>))
            {
                Dimensions = 4,
                DistanceFunction = DistanceFunction.ManhattanDistance,
                StorageName = "Vector"
            }
        };

        // Act
        var columns = SqliteVectorStoreRecordPropertyMapping.GetColumns(properties, data: data);

        // Assert
        Assert.Equal("Key", columns[0].Name);
        Assert.Equal("TEXT", columns[0].Type);
        Assert.True(columns[0].IsPrimary);
        Assert.Null(columns[0].Configuration);
        Assert.False(columns[0].HasIndex);

        if (data)
        {
            Assert.Equal("my_data", columns[1].Name);
            Assert.Equal("INTEGER", columns[1].Type);
            Assert.False(columns[1].IsPrimary);
            Assert.Null(columns[1].Configuration);
            Assert.True(columns[1].HasIndex);
        }
        else
        {
            Assert.Equal("Vector", columns[1].Name);
            Assert.Equal("FLOAT[4]", columns[1].Type);
            Assert.False(columns[1].IsPrimary);
            Assert.NotNull(columns[1].Configuration);
            Assert.False(columns[1].HasIndex);
            Assert.Equal("l1", columns[1].Configuration!["distance_metric"]);
        }
    }
}

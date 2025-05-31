// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.SemanticKernel.Connectors.SqliteVec;
using Xunit;

namespace SemanticKernel.Connectors.SqliteVec.UnitTests;

/// <summary>
/// Unit tests for <see cref="SqlitePropertyMapping"/> class.
/// </summary>
public sealed class SqlitePropertyMappingTests
{
    [Fact]
    public void MapVectorForStorageModelReturnsByteArray()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1.1f, 2.2f, 3.3f, 4.4f]);

        // Act
        var storageModelVector = SqlitePropertyMapping.MapVectorForStorageModel(vector);

        // Assert
        Assert.IsType<byte[]>(storageModelVector);
        Assert.True(storageModelVector.Length > 0);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void GetColumnsReturnsCollectionOfColumns(bool data)
    {
        // Arrange
        var properties = new List<PropertyModel>()
        {
            new KeyPropertyModel("Key", typeof(string)) { StorageName = "Key" },
            new DataPropertyModel("Data", typeof(int)) { StorageName = "my_data", IsIndexed = true },
            new VectorPropertyModel("Vector", typeof(ReadOnlyMemory<float>))
            {
                Dimensions = 4,
                DistanceFunction = DistanceFunction.ManhattanDistance,
                StorageName = "Vector"
            }
        };

        // Act
        var columns = SqlitePropertyMapping.GetColumns(properties, data: data);

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

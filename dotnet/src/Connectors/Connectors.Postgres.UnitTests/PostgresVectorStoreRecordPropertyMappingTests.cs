// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.SemanticKernel.Connectors.Postgres;
using Pgvector;
using Xunit;

namespace SemanticKernel.Connectors.Postgres.UnitTests;

/// <summary>
/// Unit tests for <see cref="PostgresVectorStoreRecordPropertyMapping"/> class.
/// </summary>
public sealed class PostgresVectorStoreRecordPropertyMappingTests
{
    [Fact]
    public void MapVectorForStorageModelWithInvalidVectorTypeThrowsException()
    {
        // Arrange
        var vector = new float[] { 1f, 2f, 3f };

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => PostgresVectorStoreRecordPropertyMapping.MapVectorForStorageModel(vector));
    }

    [Fact]
    public void MapVectorForStorageModelReturnsVector()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1.1f, 2.2f, 3.3f, 4.4f]);

        // Act
        var storageModelVector = PostgresVectorStoreRecordPropertyMapping.MapVectorForStorageModel(vector);

        // Assert
        Assert.IsType<Vector>(storageModelVector);
        Assert.True(storageModelVector.ToArray().Length > 0);
    }

    [Fact]
    public void GetPropertyValueReturnsCorrectValuesForLists()
    {
        // Arrange
        var typesAndExpectedValues = new List<(Type, object)>
        {
            (typeof(List<int>), "INTEGER[]"),
            (typeof(List<float>), "REAL[]"),
            (typeof(List<double>), "DOUBLE PRECISION[]"),
            (typeof(List<string>), "TEXT[]"),
            (typeof(List<bool>), "BOOLEAN[]"),
            (typeof(List<DateTime>), "TIMESTAMP[]"),
            (typeof(List<Guid>), "UUID[]"),
        };

        // Act & Assert
        foreach (var (type, expectedValue) in typesAndExpectedValues)
        {
            var (pgType, _) = PostgresVectorStoreRecordPropertyMapping.GetPostgresTypeName(type);
            Assert.Equal(expectedValue, pgType);
        }
    }

    [Fact]
    public void GetPropertyValueReturnsCorrectNullableValue()
    {
        // Arrange
        var typesAndExpectedValues = new List<(Type, object)>
        {
            (typeof(short), false),
            (typeof(short?), true),
            (typeof(int?), true),
            (typeof(long), false),
            (typeof(string), true),
            (typeof(bool?), true),
            (typeof(DateTime?), true),
            (typeof(Guid), false),
        };

        // Act & Assert
        foreach (var (type, expectedValue) in typesAndExpectedValues)
        {
            var (_, isNullable) = PostgresVectorStoreRecordPropertyMapping.GetPostgresTypeName(type);
            Assert.Equal(expectedValue, isNullable);
        }
    }

    [Fact]
    public void GetIndexInfoReturnsCorrectValues()
    {
        // Arrange
        List<VectorStoreRecordPropertyModel> vectorProperties =
        [
            new VectorStoreRecordVectorPropertyModel("vector1", typeof(ReadOnlyMemory<float>?)) { IndexKind = IndexKind.Hnsw, Dimensions = 1000 },
            new VectorStoreRecordVectorPropertyModel("vector2", typeof(ReadOnlyMemory<float>?)) { IndexKind = IndexKind.Flat, Dimensions = 3000 },
            new VectorStoreRecordVectorPropertyModel("vector3", typeof(ReadOnlyMemory<float>?)) { IndexKind = IndexKind.Hnsw, Dimensions = 900, DistanceFunction = DistanceFunction.ManhattanDistance },
            new VectorStoreRecordDataPropertyModel("data1", typeof(string)) { IsIndexed = true },
            new VectorStoreRecordDataPropertyModel("data2", typeof(string)) { IsIndexed = false }
        ];

        // Act
        var indexInfo = PostgresVectorStoreRecordPropertyMapping.GetIndexInfo(vectorProperties);

        // Assert
        Assert.Equal(3, indexInfo.Count);
        foreach (var (columnName, indexKind, distanceFunction, isVector) in indexInfo)
        {
            if (columnName == "vector1")
            {
                Assert.True(isVector);
                Assert.Equal(IndexKind.Hnsw, indexKind);
                Assert.Equal(DistanceFunction.CosineDistance, distanceFunction);
            }
            else if (columnName == "vector3")
            {
                Assert.True(isVector);
                Assert.Equal(IndexKind.Hnsw, indexKind);
                Assert.Equal(DistanceFunction.ManhattanDistance, distanceFunction);
            }
            else if (columnName == "data1")
            {
                Assert.False(isVector);
            }
            else
            {
                Assert.Fail("Unexpected column name");
            }
        }
    }

    [Theory]
    [InlineData(IndexKind.Hnsw, 3000)]
    public void GetVectorIndexInfoReturnsThrowsForInvalidDimensions(string indexKind, int dimensions)
    {
        // Arrange
        var vectorProperty = new VectorStoreRecordVectorPropertyModel("vector", typeof(ReadOnlyMemory<float>?)) { IndexKind = indexKind, Dimensions = dimensions };

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => PostgresVectorStoreRecordPropertyMapping.GetIndexInfo([vectorProperty]));
    }
}

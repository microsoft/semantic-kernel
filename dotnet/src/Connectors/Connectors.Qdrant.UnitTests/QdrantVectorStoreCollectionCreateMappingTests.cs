// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Qdrant.Client.Grpc;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Qdrant.UnitTests;

/// <summary>
/// Contains tests for the <see cref="QdrantVectorStoreCollectionCreateMapping"/> class.
/// </summary>
public class QdrantVectorStoreCollectionCreateMappingTests
{
    [Fact]
    public void MapSingleVectorCreatesVectorParams()
    {
        // Arrange.
        var vectorProperty = new VectorStoreRecordVectorPropertyModel("testvector", typeof(ReadOnlyMemory<float>)) { Dimensions = 4, DistanceFunction = DistanceFunction.DotProductSimilarity };

        // Act.
        var actual = QdrantVectorStoreCollectionCreateMapping.MapSingleVector(vectorProperty);

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(Distance.Dot, actual.Distance);
        Assert.Equal(4ul, actual.Size);
    }

    [Fact]
    public void MapSingleVectorDefaultsToCosine()
    {
        // Arrange.
        var vectorProperty = new VectorStoreRecordVectorPropertyModel("testvector", typeof(ReadOnlyMemory<float>)) { Dimensions = 4 };

        // Act.
        var actual = QdrantVectorStoreCollectionCreateMapping.MapSingleVector(vectorProperty);

        // Assert.
        Assert.Equal(Distance.Cosine, actual.Distance);
    }

    [Fact]
    public void MapSingleVectorThrowsForUnsupportedDistanceFunction()
    {
        // Arrange.
        var vectorProperty = new VectorStoreRecordVectorPropertyModel("testvector", typeof(ReadOnlyMemory<float>)) { Dimensions = 4, DistanceFunction = DistanceFunction.CosineDistance };

        // Act and assert.
        Assert.Throws<InvalidOperationException>(() => QdrantVectorStoreCollectionCreateMapping.MapSingleVector(vectorProperty));
    }

    [Fact]
    public void MapNamedVectorsCreatesVectorParamsMap()
    {
        // Arrange.
        var vectorProperties = new VectorStoreRecordVectorPropertyModel[]
        {
            new("testvector1", typeof(ReadOnlyMemory<float>))
            {
                Dimensions = 10,
                DistanceFunction = DistanceFunction.EuclideanDistance,
                StorageName = "storage_testvector1"
            },
            new("testvector2", typeof(ReadOnlyMemory<float>))
            {
                Dimensions = 20,
                StorageName = "storage_testvector2"
            }
        };

        // Act.
        var actual = QdrantVectorStoreCollectionCreateMapping.MapNamedVectors(vectorProperties);

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(2, actual.Map.Count);
        Assert.Equal(10ul, actual.Map["storage_testvector1"].Size);
        Assert.Equal(Distance.Euclid, actual.Map["storage_testvector1"].Distance);
        Assert.Equal(20ul, actual.Map["storage_testvector2"].Size);
        Assert.Equal(Distance.Cosine, actual.Map["storage_testvector2"].Distance);
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Moq;
using Qdrant.Client.Grpc;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Qdrant.UnitTests;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete

/// <summary>
/// Contains tests for the <see cref="QdrantVectorStoreCollectionSearchMapping"/> class.
/// </summary>
public class QdrantVectorStoreCollectionSearchMappingTests
{
    [Fact]
    public void MapScoredPointToVectorSearchResultMapsResults()
    {
        // Arrange.
        var scoredPoint = new ScoredPoint
        {
            Id = 1,
            Payload = { ["storage_DataField"] = "data 1" },
            Vectors = new float[] { 1, 2, 3 },
            Score = 0.5f
        };

        var mapperMock = new Mock<IVectorStoreRecordMapper<DataModel, PointStruct>>(MockBehavior.Strict);
        mapperMock.Setup(x => x.MapFromStorageToDataModel(It.IsAny<PointStruct>(), It.IsAny<StorageToDataModelMapperOptions>())).Returns(new DataModel { Id = 1, DataField = "data 1", Embedding = new float[] { 1, 2, 3 } });

        // Act.
        var actual = QdrantVectorStoreCollectionSearchMapping.MapScoredPointToVectorSearchResult<DataModel>(scoredPoint, mapperMock.Object, true, "Qdrant", "mycollection", "query");

        // Assert.
        Assert.Equal(1ul, actual.Record.Id);
        Assert.Equal("data 1", actual.Record.DataField);
        Assert.Equal(new float[] { 1, 2, 3 }, actual.Record.Embedding.ToArray());
        Assert.Equal(0.5f, actual.Score);
    }

    public class DataModel
    {
        public ulong Id { get; init; }

        public string? DataField { get; init; }

        public ReadOnlyMemory<float> Embedding { get; init; }
    }
}

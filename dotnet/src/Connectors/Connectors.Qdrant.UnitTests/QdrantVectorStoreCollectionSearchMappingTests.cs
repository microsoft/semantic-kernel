// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
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
    [Theory]
    [InlineData("string")]
    [InlineData("int")]
    [InlineData("bool")]
    [InlineData("long")]

    public void BuildFilterMapsEqualityClause(string type)
    {
        // Arrange.
        object expected = type switch
        {
            "string" => "Value",
            "int" => 1,
            "bool" => true,
            "long" => 1L,
            _ => throw new InvalidOperationException()
        };
        var filter = new VectorSearchFilter().EqualTo("FieldName", expected);

        // Act.
        var actual = QdrantVectorStoreCollectionSearchMapping.BuildFromLegacyFilter(filter, new Dictionary<string, string>() { { "FieldName", "storage_FieldName" } });

        // Assert.
        Assert.Single(actual.Must);
        Assert.Equal("storage_FieldName", actual.Must.First().Field.Key);

        var match = actual.Must.First().Field.Match;
        object actualSearchValue = type switch
        {
            "string" => match.Keyword,
            "int" => match.Integer,
            "bool" => match.Boolean,
            "long" => match.Integer,
            _ => throw new InvalidOperationException()
        };

        if (type == "int")
        {
            // Qdrant uses long for integers so we have to cast the expected value to long.
            Assert.Equal((long)(int)expected, actualSearchValue);
        }
        else
        {
            Assert.Equal(expected, actualSearchValue);
        }
    }

    [Fact]
    public void BuildFilterMapsTagContainsClause()
    {
        // Arrange.
        var filter = new VectorSearchFilter().AnyTagEqualTo("FieldName", "Value");

        // Act.
        var actual = QdrantVectorStoreCollectionSearchMapping.BuildFromLegacyFilter(filter, new Dictionary<string, string>() { { "FieldName", "storage_FieldName" } });

        // Assert.
        Assert.Single(actual.Must);
        Assert.Equal("storage_FieldName", actual.Must.First().Field.Key);
        Assert.Equal("Value", actual.Must.First().Field.Match.Keyword);
    }

    [Fact]
    public void BuildFilterThrowsForUnknownFieldName()
    {
        // Arrange.
        var filter = new VectorSearchFilter().EqualTo("FieldName", "Value");

        // Act and Assert.
        Assert.Throws<InvalidOperationException>(() => QdrantVectorStoreCollectionSearchMapping.BuildFromLegacyFilter(filter, new Dictionary<string, string>()));
    }

    [Fact]
    public void MapScoredPointToVectorSearchResultMapsResults()
    {
        var responseVector = VectorOutput.Parser.ParseJson("{ \"data\": [1, 2, 3] }");

        // Arrange.
        var scoredPoint = new ScoredPoint
        {
            Id = 1,
            Payload = { ["storage_DataField"] = "data 1" },
            Vectors = new VectorsOutput() { Vector = responseVector },
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

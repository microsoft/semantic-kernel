// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Xunit;

namespace SemanticKernel.Connectors.Weaviate.UnitTests;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete

/// <summary>
/// Unit tests for <see cref="WeaviateVectorStoreRecordCollectionQueryBuilder"/> class.
/// </summary>
public sealed class WeaviateVectorStoreRecordCollectionQueryBuilderTests
{
    private const string CollectionName = "Collection";
    private const string VectorPropertyName = "descriptionEmbedding";

    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
        Converters =
        {
            new WeaviateDateTimeOffsetConverter(),
            new WeaviateNullableDateTimeOffsetConverter()
        }
    };

    private readonly VectorStoreRecordModel _model = new WeaviateModelBuilder(hasNamedVectors: true)
        .Build(
            typeof(Dictionary<string, object?>),
            new()
            {
                Properties =
                [
                    new VectorStoreRecordKeyProperty("HotelId", typeof(Guid)) { StoragePropertyName = "hotelId" },
                    new VectorStoreRecordDataProperty("HotelName", typeof(string)) { StoragePropertyName = "hotelName" },
                    new VectorStoreRecordDataProperty("HotelCode", typeof(string)) { StoragePropertyName = "hotelCode" },
                    new VectorStoreRecordDataProperty("Tags", typeof(string[])) { StoragePropertyName = "tags" },
                    new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>), 10) { StoragePropertyName = "descriptionEmbeddding" },
                ]
            },
            defaultEmbeddingGenerator: null);

    private readonly ReadOnlyMemory<float> _vector = new([31f, 32f, 33f, 34f]);

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void BuildSearchQueryByDefaultReturnsValidQuery(bool hasNamedVectors)
    {
        // Arrange
        var expectedQuery = $$"""
        {
          Get {
            Collection (
              limit: 3
              offset: 2
              {{string.Empty}}
              nearVector: {
                {{(hasNamedVectors ? "targetVectors: [\"descriptionEmbedding\"]" : string.Empty)}}
                vector: [31,32,33,34]
              }
            ) {
              HotelName HotelCode Tags
              _additional {
                id
                distance
                {{string.Empty}}
              }
            }
          }
        }
        """;

        var searchOptions = new VectorSearchOptions<DummyType>
        {
            Skip = 2,
        };

        // Act
        var query = WeaviateVectorStoreRecordCollectionQueryBuilder.BuildSearchQuery(
            this._vector,
            CollectionName,
            VectorPropertyName,
            s_jsonSerializerOptions,
            top: 3,
            searchOptions,
            this._model,
            hasNamedVectors);

        // Assert
        Assert.Equal(expectedQuery, query);

        Assert.DoesNotContain("vectors", query);
        Assert.DoesNotContain("where", query);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void BuildSearchQueryWithIncludedVectorsReturnsValidQuery(bool hasNamedVectors)
    {
        // Arrange
        var searchOptions = new VectorSearchOptions<DummyType>
        {
            Skip = 2,
            IncludeVectors = true
        };

        // Act
        var query = WeaviateVectorStoreRecordCollectionQueryBuilder.BuildSearchQuery(
            this._vector,
            CollectionName,
            VectorPropertyName,
            s_jsonSerializerOptions,
            top: 3,
            searchOptions,
            this._model,
            hasNamedVectors);

        // Assert
        var vectorQuery = hasNamedVectors ? "vectors { DescriptionEmbedding }" : "vector";

        Assert.Contains(vectorQuery, query);
    }

    [Fact]
    public void BuildSearchQueryWithFilterReturnsValidQuery()
    {
        // Arrange
        const string ExpectedFirstSubquery = """{ path: ["HotelName"], operator: Equal, valueText: "Test Name" }""";
        const string ExpectedSecondSubquery = """{ path: ["Tags"], operator: ContainsAny, valueText: ["t1"] }""";

        var searchOptions = new VectorSearchOptions<DummyType>
        {
            Skip = 2,
            OldFilter = new VectorSearchFilter()
                .EqualTo("HotelName", "Test Name")
                .AnyTagEqualTo("Tags", "t1")
        };

        // Act
        var query = WeaviateVectorStoreRecordCollectionQueryBuilder.BuildSearchQuery(
            this._vector,
            CollectionName,
            VectorPropertyName,
            s_jsonSerializerOptions,
            top: 3,
            searchOptions,
            this._model,
            hasNamedVectors: true);

        // Assert
        Assert.Contains(ExpectedFirstSubquery, query);
        Assert.Contains(ExpectedSecondSubquery, query);
    }

    [Fact]
    public void BuildSearchQueryWithInvalidFilterValueThrowsException()
    {
        // Arrange
        var searchOptions = new VectorSearchOptions<DummyType>
        {
            Skip = 2,
            OldFilter = new VectorSearchFilter().EqualTo("HotelName", new TestFilterValue())
        };

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => WeaviateVectorStoreRecordCollectionQueryBuilder.BuildSearchQuery(
            this._vector,
            CollectionName,
            VectorPropertyName,
            s_jsonSerializerOptions,
            top: 3,
            searchOptions,
            this._model,
            hasNamedVectors: true));
    }

    [Fact]
    public void BuildSearchQueryWithNonExistentPropertyInFilterThrowsException()
    {
        // Arrange
        var searchOptions = new VectorSearchOptions<DummyType>
        {
            Skip = 2,
            OldFilter = new VectorSearchFilter().EqualTo("NonExistentProperty", "value")
        };

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => WeaviateVectorStoreRecordCollectionQueryBuilder.BuildSearchQuery(
            this._vector,
            CollectionName,
            VectorPropertyName,
            s_jsonSerializerOptions,
            top: 3,
            searchOptions,
            this._model,
            hasNamedVectors: true));
    }

    #region private

#pragma warning disable CA1812 // An internal class that is apparently never instantiated. If so, remove the code from the assembly.
    private sealed class DummyType;
#pragma warning restore CA1812
    private sealed class TestFilterValue;

    #endregion
}

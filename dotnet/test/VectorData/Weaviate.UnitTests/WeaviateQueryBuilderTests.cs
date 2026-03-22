// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Xunit;

namespace SemanticKernel.Connectors.Weaviate.UnitTests;

/// <summary>
/// Unit tests for <see cref="WeaviateQueryBuilder"/> class.
/// </summary>
public sealed class WeaviateQueryBuilderTests
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

    private readonly CollectionModel _model = new WeaviateModelBuilder(hasNamedVectors: true)
        .BuildDynamic(
            new()
            {
                Properties =
                [
                    new VectorStoreKeyProperty("HotelId", typeof(Guid)) { StorageName = "hotelId" },
                    new VectorStoreDataProperty("HotelName", typeof(string)) { StorageName = "hotelName" },
                    new VectorStoreDataProperty("HotelCode", typeof(string)) { StorageName = "hotelCode" },
                    new VectorStoreDataProperty("Tags", typeof(string[])) { StorageName = "tags" },
                    new VectorStoreVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>), 10) { StorageName = "descriptionEmbeddding" },
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
                {{string.Empty}}
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
        var query = WeaviateQueryBuilder.BuildSearchQuery(
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
        var query = WeaviateQueryBuilder.BuildSearchQuery(
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
    public void BuildHybridSearchQueryEscapesDoubleQuotesInKeywords()
    {
        // Arrange
        var searchOptions = new HybridSearchOptions<DummyType> { Skip = 0 };
        var vectorProperty = this._model.VectorProperties[0];
        var textProperty = this._model.DataProperties[0];

        // Act
        var query = WeaviateQueryBuilder.BuildHybridSearchQuery(
            this._vector,
            top: 3,
            keywords: "test \"injection\"",
            CollectionName,
            this._model,
            vectorProperty,
            textProperty,
            s_jsonSerializerOptions,
            searchOptions,
            hasNamedVectors: true);

        // Assert - the double quote must be escaped in the GraphQL string
        Assert.Contains("query: \"test \\\"injection\\\"\"", query);
    }

    [Fact]
    public void BuildHybridSearchQueryEscapesBackslashInKeywords()
    {
        // Arrange
        var searchOptions = new HybridSearchOptions<DummyType> { Skip = 0 };
        var vectorProperty = this._model.VectorProperties[0];
        var textProperty = this._model.DataProperties[0];

        // Act
        var query = WeaviateQueryBuilder.BuildHybridSearchQuery(
            this._vector,
            top: 3,
            keywords: @"test\path",
            CollectionName,
            this._model,
            vectorProperty,
            textProperty,
            s_jsonSerializerOptions,
            searchOptions,
            hasNamedVectors: true);

        // Assert - backslash must be escaped
        Assert.Contains(@"query: ""test\\path""", query);
    }

    [Fact]
    public void BuildHybridSearchQueryWithPlainKeywordsWorks()
    {
        // Arrange
        var searchOptions = new HybridSearchOptions<DummyType> { Skip = 0 };
        var vectorProperty = this._model.VectorProperties[0];
        var textProperty = this._model.DataProperties[0];

        // Act
        var query = WeaviateQueryBuilder.BuildHybridSearchQuery(
            this._vector,
            top: 3,
            keywords: "hello world",
            CollectionName,
            this._model,
            vectorProperty,
            textProperty,
            s_jsonSerializerOptions,
            searchOptions,
            hasNamedVectors: true);

        // Assert
        Assert.Contains("query: \"hello world\"", query);
    }

    #region private

#pragma warning disable CA1812 // An internal class that is apparently never instantiated. If so, remove the code from the assembly.
    private sealed class DummyType;
#pragma warning restore CA1812

    #endregion
}

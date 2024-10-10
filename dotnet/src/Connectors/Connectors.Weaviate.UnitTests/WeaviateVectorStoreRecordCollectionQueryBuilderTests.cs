﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Microsoft.SemanticKernel.Data;
using Xunit;

namespace SemanticKernel.Connectors.Weaviate.UnitTests;

/// <summary>
/// Unit tests for <see cref="WeaviateVectorStoreRecordCollectionQueryBuilder"/> class.
/// </summary>
public sealed class WeaviateVectorStoreRecordCollectionQueryBuilderTests
{
    private const string CollectionName = "Collection";
    private const string VectorPropertyName = "descriptionEmbedding";
    private const string KeyPropertyName = "HotelId";

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

    private readonly Dictionary<string, string> _storagePropertyNames = new()
    {
        ["HotelId"] = "hotelId",
        ["HotelName"] = "hotelName",
        ["HotelCode"] = "hotelCode",
        ["Tags"] = "tags",
        ["DescriptionEmbedding"] = "descriptionEmbedding"
    };

    private readonly ReadOnlyMemory<float> _vector = new([31f, 32f, 33f, 34f]);

    private readonly List<string> _vectorPropertyStorageNames = ["descriptionEmbedding"];

    private readonly List<string> _dataPropertyStorageNames = ["hotelName", "hotelCode"];

    [Fact]
    public void BuildSearchQueryByDefaultReturnsValidQuery()
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
                targetVectors: ["descriptionEmbedding"]
                vector: [31,32,33,34]
              }
            ) {
              hotelName hotelCode
              _additional {
                id
                distance
                {{string.Empty}}
              }
            }
          }
        }
        """;

        var searchOptions = new VectorSearchOptions
        {
            Skip = 2,
            Top = 3,
            VectorPropertyName = "DescriptionEmbedding"
        };

        // Act
        var query = WeaviateVectorStoreRecordCollectionQueryBuilder.BuildSearchQuery(
            this._vector,
            CollectionName,
            VectorPropertyName,
            KeyPropertyName,
            s_jsonSerializerOptions,
            searchOptions,
            this._storagePropertyNames,
            this._vectorPropertyStorageNames,
            this._dataPropertyStorageNames);

        // Assert
        Assert.Equal(expectedQuery, query);

        Assert.DoesNotContain("vectors", query);
        Assert.DoesNotContain("where", query);
    }

    [Fact]
    public void BuildSearchQueryWithIncludedVectorsReturnsValidQuery()
    {
        // Arrange
        var searchOptions = new VectorSearchOptions
        {
            Skip = 2,
            Top = 3,
            VectorPropertyName = "DescriptionEmbedding",
            IncludeVectors = true
        };

        // Act
        var query = WeaviateVectorStoreRecordCollectionQueryBuilder.BuildSearchQuery(
            this._vector,
            CollectionName,
            VectorPropertyName,
            KeyPropertyName,
            s_jsonSerializerOptions,
            searchOptions,
            this._storagePropertyNames,
            this._vectorPropertyStorageNames,
            this._dataPropertyStorageNames);

        // Assert
        Assert.Contains("vectors { descriptionEmbedding }", query);
    }

    [Fact]
    public void BuildSearchQueryWithFilterReturnsValidQuery()
    {
        // Arrange
        const string ExpectedFirstSubquery = """{ path: ["hotelName"], operator: Equal, valueText: "Test Name" }""";
        const string ExpectedSecondSubquery = """{ path: ["tags"], operator: ContainsAny, valueText: ["t1"] }""";

        var searchOptions = new VectorSearchOptions
        {
            Skip = 2,
            Top = 3,
            VectorPropertyName = "DescriptionEmbedding",
            Filter = new VectorSearchFilter()
                .EqualTo("HotelName", "Test Name")
                .AnyTagEqualTo("Tags", "t1")
        };

        // Act
        var query = WeaviateVectorStoreRecordCollectionQueryBuilder.BuildSearchQuery(
            this._vector,
            CollectionName,
            VectorPropertyName,
            KeyPropertyName,
            s_jsonSerializerOptions,
            searchOptions,
            this._storagePropertyNames,
            this._vectorPropertyStorageNames,
            this._dataPropertyStorageNames);

        // Assert
        Assert.Contains(ExpectedFirstSubquery, query);
        Assert.Contains(ExpectedSecondSubquery, query);
    }

    [Fact]
    public void BuildSearchQueryWithInvalidFilterValueThrowsException()
    {
        // Arrange
        var searchOptions = new VectorSearchOptions
        {
            Skip = 2,
            Top = 3,
            VectorPropertyName = "DescriptionEmbedding",
            Filter = new VectorSearchFilter().EqualTo("HotelName", new TestFilterValue())
        };

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => WeaviateVectorStoreRecordCollectionQueryBuilder.BuildSearchQuery(
            this._vector,
            CollectionName,
            VectorPropertyName,
            KeyPropertyName,
            s_jsonSerializerOptions,
            searchOptions,
            this._storagePropertyNames,
            this._vectorPropertyStorageNames,
            this._dataPropertyStorageNames));
    }

    [Fact]
    public void BuildSearchQueryWithNonExistentPropertyInFilterThrowsException()
    {
        // Arrange
        var searchOptions = new VectorSearchOptions
        {
            Skip = 2,
            Top = 3,
            VectorPropertyName = "DescriptionEmbedding",
            Filter = new VectorSearchFilter().EqualTo("NonExistentProperty", "value")
        };

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => WeaviateVectorStoreRecordCollectionQueryBuilder.BuildSearchQuery(
            this._vector,
            CollectionName,
            VectorPropertyName,
            KeyPropertyName,
            s_jsonSerializerOptions,
            searchOptions,
            this._storagePropertyNames,
            this._vectorPropertyStorageNames,
            this._dataPropertyStorageNames));
    }

    #region private

    private sealed class TestFilterValue;

    #endregion
}

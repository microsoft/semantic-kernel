// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Data;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains tests for the <see cref="RedisVectorStoreCollectionSearchMapping"/> class.
/// </summary>
public class RedisVectorStoreCollectionSearchMappingTests
{
    [Fact]
    public void BuildQueryBuildsRedisQueryWithDefaults()
    {
        // Arrange.
        var floatVectorQuery = VectorSearchQuery.CreateQuery(
            new ReadOnlyMemory<float>(new float[] { 1.0f, 2.0f, 3.0f }));
        var storagePropertyNames = new Dictionary<string, string>()
        {
            { "Vector", "storage_Vector" },
        };
        var firstVectorPropertyName = "storage_Vector";

        // Act.
        var query = RedisVectorStoreCollectionSearchMapping.BuildQuery(floatVectorQuery, storagePropertyNames, firstVectorPropertyName, null);

        // Assert.
        Assert.NotNull(query);
        Assert.Equal("*=>[KNN 3 @storage_Vector $embedding AS vector_score]", query.QueryString);
        Assert.Equal("vector_score", query.SortBy);
        Assert.True(query.WithScores);
        Assert.Equal(2, query.dialect);
    }

    [Fact]
    public void BuildQueryBuildsRedisQueryWithCustomVectorName()
    {
        // Arrange.
        var floatVectorQuery = VectorSearchQuery.CreateQuery(
            new ReadOnlyMemory<float>(new float[] { 1.0f, 2.0f, 3.0f }),
            new VectorSearchOptions { Limit = 5, Offset = 3, VectorFieldName = "Vector" });
        var storagePropertyNames = new Dictionary<string, string>()
        {
            { "Vector", "storage_Vector" },
        };
        var firstVectorPropertyName = "storage_FirstVector";
        var selectFields = new string[] { "storage_Field1", "storage_Field2" };

        // Act.
        var query = RedisVectorStoreCollectionSearchMapping.BuildQuery(floatVectorQuery, storagePropertyNames, firstVectorPropertyName, selectFields);

        // Assert.
        Assert.NotNull(query);
        Assert.Equal("*=>[KNN 5 @storage_Vector $embedding AS vector_score]", query.QueryString);
    }

    [Fact]
    public void BuildQueryFailsForInvalidVectorName()
    {
        // Arrange.
        var floatVectorQuery = VectorSearchQuery.CreateQuery(
            new ReadOnlyMemory<float>(new float[] { 1.0f, 2.0f, 3.0f }),
            new VectorSearchOptions { VectorFieldName = "UnknownVector" });
        var storagePropertyNames = new Dictionary<string, string>()
        {
            { "Vector", "storage_Vector" },
        };
        var firstVectorPropertyName = "storage_FirstVector";

        // Act & Assert.
        Assert.Throws<InvalidOperationException>(() =>
        {
            var query = RedisVectorStoreCollectionSearchMapping.BuildQuery(floatVectorQuery, storagePropertyNames, firstVectorPropertyName, null);
        });
    }

    [Theory]
    [InlineData("stringEquality")]
    [InlineData("intEquality")]
    [InlineData("longEquality")]
    [InlineData("floatEquality")]
    [InlineData("doubleEquality")]
    [InlineData("tagContains")]
    public void BuildFilterBuildsEqualityFilter(string filterType)
    {
        // Arrange.
        var basicVectorSearchFilter = filterType switch
        {
            "stringEquality" => new VectorSearchFilter().Equality("Data1", "my value"),
            "intEquality" => new VectorSearchFilter().Equality("Data1", 3),
            "longEquality" => new VectorSearchFilter().Equality("Data1", 3L),
            "floatEquality" => new VectorSearchFilter().Equality("Data1", 3.3f),
            "doubleEquality" => new VectorSearchFilter().Equality("Data1", 3.3),
            "tagContains" => new VectorSearchFilter().TagListContains("Data1", "my value"),
            _ => throw new InvalidOperationException(),
        };

        var storagePropertyNames = new Dictionary<string, string>()
        {
            { "Data1", "storage_Data1" },
        };

        // Act.
        var filter = RedisVectorStoreCollectionSearchMapping.BuildFilter(basicVectorSearchFilter, storagePropertyNames);

        // Assert.
        switch (filterType)
        {
            case "stringEquality":
                Assert.Equal("(@storage_Data1:{my value})", filter);
                break;
            case "intEquality":
            case "longEquality":
                Assert.Equal("(@storage_Data1:[3 3])", filter);
                break;
            case "floatEquality":
            case "doubleEquality":
                Assert.Equal("(@storage_Data1:[3.3 3.3])", filter);
                break;
            case "tagContains":
                Assert.Equal("(@storage_Data1:{my value})", filter);
                break;
        }
    }

    [Fact]
    public void BuildFilterThrowsForInvalidValueType()
    {
        // Arrange.
        var basicVectorSearchFilter = new VectorSearchFilter().Equality("Data1", true);
        var storagePropertyNames = new Dictionary<string, string>()
        {
            { "Data1", "storage_Data1" },
        };

        // Act & Assert.
        Assert.Throws<InvalidOperationException>(() =>
        {
            var filter = RedisVectorStoreCollectionSearchMapping.BuildFilter(basicVectorSearchFilter, storagePropertyNames);
        });
    }

    [Fact]
    public void BuildFilterThrowsForUnknownFieldName()
    {
        // Arrange.
        var basicVectorSearchFilter = new VectorSearchFilter().Equality("UnknownData", "value");
        var storagePropertyNames = new Dictionary<string, string>()
        {
            { "Data1", "storage_Data1" },
        };

        // Act & Assert.
        Assert.Throws<InvalidOperationException>(() =>
        {
            var filter = RedisVectorStoreCollectionSearchMapping.BuildFilter(basicVectorSearchFilter, storagePropertyNames);
        });
    }
}

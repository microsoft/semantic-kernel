// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Xunit;

namespace SemanticKernel.Connectors.AzureCosmosDBNoSQL.UnitTests;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete

/// <summary>
/// Unit tests for <see cref="AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder"/> class.
/// </summary>
public sealed class AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilderTests
{
    private const string ScorePropertyName = "TestScore";

    private readonly Dictionary<string, string> _storagePropertyNames = new()
    {
        ["TestProperty1"] = "test_property_1",
        ["TestProperty2"] = "test_property_2",
        ["TestProperty3"] = "test_property_3",
    };

    [Fact]
    public void BuildSearchQueryByDefaultReturnsValidQueryDefinition()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1f, 2f, 3f]);
        var vectorPropertyName = "test_property_1";
        var fields = this._storagePropertyNames.Values.ToList();

        var filter = new VectorSearchFilter()
            .EqualTo("TestProperty2", "test-value-2")
            .AnyTagEqualTo("TestProperty3", "test-value-3");

        // Act
        var queryDefinition = AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSearchQuery<ReadOnlyMemory<float>, DummyType>(
            vector,
            keywords: null,
            fields,
            this._storagePropertyNames,
            vectorPropertyName,
            textPropertyName: null,
            ScorePropertyName,
            oldFilter: filter,
            filter: null,
            10,
            5);

        var queryText = queryDefinition.QueryText;
        var queryParameters = queryDefinition.GetQueryParameters();

        // Assert
        Assert.Contains("SELECT x.test_property_1,x.test_property_2,x.test_property_3,VectorDistance(x.test_property_1, @vector) AS TestScore", queryText);
        Assert.Contains("FROM x", queryText);
        Assert.Contains("WHERE x.test_property_2 = @cv0 AND ARRAY_CONTAINS(x.test_property_3, @cv1)", queryText);
        Assert.Contains("ORDER BY VectorDistance(x.test_property_1, @vector)", queryText);
        Assert.Contains("OFFSET 5 LIMIT 10", queryText);

        Assert.Equal("@vector", queryParameters[0].Name);
        Assert.Equal(vector, queryParameters[0].Value);

        Assert.Equal("@cv0", queryParameters[1].Name);
        Assert.Equal("test-value-2", queryParameters[1].Value);

        Assert.Equal("@cv1", queryParameters[2].Name);
        Assert.Equal("test-value-3", queryParameters[2].Value);
    }

    [Fact]
    public void BuildSearchQueryWithoutOffsetReturnsQueryDefinitionWithTopParameter()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1f, 2f, 3f]);
        var vectorPropertyName = "test_property_1";
        var fields = this._storagePropertyNames.Values.ToList();

        var filter = new VectorSearchFilter()
            .EqualTo("TestProperty2", "test-value-2")
            .AnyTagEqualTo("TestProperty3", "test-value-3");

        // Act
        var queryDefinition = AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSearchQuery<ReadOnlyMemory<float>, DummyType>(
            vector,
            keywords: null,
            fields,
            this._storagePropertyNames,
            vectorPropertyName,
            textPropertyName: null,
            ScorePropertyName,
            oldFilter: filter,
            filter: null,
            10,
            0);

        var queryText = queryDefinition.QueryText;
        var queryParameters = queryDefinition.GetQueryParameters();

        // Assert
        Assert.Contains("SELECT TOP 10 x.test_property_1,x.test_property_2,x.test_property_3,VectorDistance(x.test_property_1, @vector) AS TestScore", queryText);
        Assert.Contains("FROM x", queryText);
        Assert.Contains("WHERE x.test_property_2 = @cv0 AND ARRAY_CONTAINS(x.test_property_3, @cv1)", queryText);
        Assert.Contains("ORDER BY VectorDistance(x.test_property_1, @vector)", queryText);

        Assert.DoesNotContain("OFFSET 0 LIMIT 10", queryText);

        Assert.Equal("@vector", queryParameters[0].Name);
        Assert.Equal(vector, queryParameters[0].Value);

        Assert.Equal("@cv0", queryParameters[1].Name);
        Assert.Equal("test-value-2", queryParameters[1].Value);

        Assert.Equal("@cv1", queryParameters[2].Name);
        Assert.Equal("test-value-3", queryParameters[2].Value);
    }

    [Fact]
    public void BuildSearchQueryWithInvalidFilterThrowsException()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1f, 2f, 3f]);
        var vectorPropertyName = "test_property_1";
        var fields = this._storagePropertyNames.Values.ToList();

        var filter = new VectorSearchFilter().EqualTo("non-existent-property", "test-value-2");

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() =>
            AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSearchQuery<ReadOnlyMemory<float>, DummyType>(
                vector,
                keywords: null,
                fields,
                this._storagePropertyNames,
                vectorPropertyName,
                textPropertyName: null,
                ScorePropertyName,
                oldFilter: filter,
                filter: null,
                10,
                5));
    }

    [Fact]
    public void BuildSearchQueryWithoutFilterDoesNotContainWhereClause()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1f, 2f, 3f]);
        var vectorPropertyName = "test_property_1";
        var fields = this._storagePropertyNames.Values.ToList();

        // Act
        var queryDefinition = AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSearchQuery<ReadOnlyMemory<float>, DummyType>(
            vector,
            keywords: null,
            fields,
            this._storagePropertyNames,
            vectorPropertyName,
            textPropertyName: null,
            ScorePropertyName,
            oldFilter: null,
            filter: null,
            10,
            5);

        var queryText = queryDefinition.QueryText;
        var queryParameters = queryDefinition.GetQueryParameters();

        // Assert
        Assert.DoesNotContain("WHERE", queryText);
        Assert.Contains("OFFSET 5 LIMIT 10", queryText);

        Assert.Equal("@vector", queryParameters[0].Name);
        Assert.Equal(vector, queryParameters[0].Value);
    }

    [Fact]
    public void BuildSelectQueryByDefaultReturnsValidQueryDefinition()
    {
        // Arrange
        const string ExpectedQueryText = """
                                         SELECT x.key,x.property_1,x.property_2
                                         FROM x
                                         WHERE (x.key_property = @rk0  AND  x.partition_key_property = @pk0)
                                         """;

        const string KeyStoragePropertyName = "key_property";
        const string PartitionKeyPropertyName = "partition_key_property";

        var keys = new List<AzureCosmosDBNoSQLCompositeKey> { new("key", "partition_key") };
        var fields = new List<string> { "key", "property_1", "property_2" };

        // Act
        var queryDefinition = AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSelectQuery(
            KeyStoragePropertyName,
            PartitionKeyPropertyName,
            keys,
            fields);

        var queryText = queryDefinition.QueryText;
        var queryParameters = queryDefinition.GetQueryParameters();

        // Assert
        Assert.Equal(ExpectedQueryText, queryText);

        Assert.Equal("@rk0", queryParameters[0].Name);
        Assert.Equal("key", queryParameters[0].Value);

        Assert.Equal("@pk0", queryParameters[1].Name);
        Assert.Equal("partition_key", queryParameters[1].Value);
    }

    [Fact]
    public void BuildSearchQueryWithHybridFieldsReturnsValidHybridQueryDefinition()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1f, 2f, 3f]);
        var keywordText = "hybrid";
        var vectorPropertyName = "test_property_1";
        var textPropertyName = "test_property_2";
        var fields = this._storagePropertyNames.Values.ToList();

        var filter = new VectorSearchFilter()
            .EqualTo("TestProperty2", "test-value-2")
            .AnyTagEqualTo("TestProperty3", "test-value-3");

        // Act
        var queryDefinition = AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSearchQuery<ReadOnlyMemory<float>, DummyType>(
            vector,
            [keywordText],
            fields,
            this._storagePropertyNames,
            vectorPropertyName,
            textPropertyName,
            ScorePropertyName,
            oldFilter: filter,
            filter: null,
            10,
            5);

        var queryText = queryDefinition.QueryText;
        var queryParameters = queryDefinition.GetQueryParameters();

        // Assert
        Assert.Contains("SELECT x.test_property_1,x.test_property_2,x.test_property_3,VectorDistance(x.test_property_1, @vector) AS TestScore", queryText);
        Assert.Contains("FROM x", queryText);
        Assert.Contains("WHERE x.test_property_2 = @cv0 AND ARRAY_CONTAINS(x.test_property_3, @cv1)", queryText);
        Assert.Contains("ORDER BY RANK RRF(VectorDistance(x.test_property_1, @vector), FullTextScore(x.test_property_2, [\"hybrid\"]))", queryText);
        Assert.Contains("OFFSET 5 LIMIT 10", queryText);

        Assert.Equal("@vector", queryParameters[0].Name);
        Assert.Equal(vector, queryParameters[0].Value);

        Assert.Equal("@cv0", queryParameters[1].Name);
        Assert.Equal("test-value-2", queryParameters[1].Value);

        Assert.Equal("@cv1", queryParameters[2].Name);
        Assert.Equal("test-value-3", queryParameters[2].Value);
    }

#pragma warning disable CA1812 // An internal class that is apparently never instantiated. If so, remove the code from the assembly.
    private sealed class DummyType;
#pragma warning restore CA1812
}

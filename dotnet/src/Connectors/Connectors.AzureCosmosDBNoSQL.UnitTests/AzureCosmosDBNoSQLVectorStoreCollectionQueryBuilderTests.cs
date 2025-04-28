// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
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

    private readonly VectorStoreRecordModel _model = new AzureCosmosDBNoSQLVectorStoreModelBuilder().Build(
        typeof(Dictionary<string, object?>),
        new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty("Key", typeof(string)),
                new VectorStoreRecordVectorProperty("TestProperty1", typeof(ReadOnlyMemory<float>), 10) { StoragePropertyName = "test_property_1" },
                new VectorStoreRecordDataProperty("TestProperty2", typeof(string)) { StoragePropertyName = "test_property_2" },
                new VectorStoreRecordDataProperty("TestProperty3", typeof(string)) { StoragePropertyName = "test_property_3" }
            ]
        },
        defaultEmbeddingGenerator: null);

    [Fact]
    public void BuildSearchQueryByDefaultReturnsValidQueryDefinition()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1f, 2f, 3f]);
        var vectorPropertyName = "test_property_1";

        var filter = new VectorSearchFilter()
            .EqualTo("TestProperty2", "test-value-2")
            .AnyTagEqualTo("TestProperty3", "test-value-3");

        // Act
        var queryDefinition = AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSearchQuery<ReadOnlyMemory<float>, DummyType>(
            vector,
            keywords: null,
            this._model,
            vectorPropertyName,
            textPropertyName: null,
            ScorePropertyName,
            oldFilter: filter,
            filter: null,
            10,
            5,
            includeVectors: true);

        var queryText = queryDefinition.QueryText;
        var queryParameters = queryDefinition.GetQueryParameters();

        // Assert
        Assert.Contains("SELECT x.id,x.TestProperty1,x.TestProperty2,x.TestProperty3,VectorDistance(x.test_property_1, @vector) AS TestScore", queryText);
        Assert.Contains("FROM x", queryText);
        Assert.Contains("WHERE x.TestProperty2 = @cv0 AND ARRAY_CONTAINS(x.TestProperty3, @cv1)", queryText);
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

        var filter = new VectorSearchFilter()
            .EqualTo("TestProperty2", "test-value-2")
            .AnyTagEqualTo("TestProperty3", "test-value-3");

        // Act
        var queryDefinition = AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSearchQuery<ReadOnlyMemory<float>, DummyType>(
            vector,
            keywords: null,
            this._model,
            vectorPropertyName,
            textPropertyName: null,
            ScorePropertyName,
            oldFilter: filter,
            filter: null,
            10,
            0,
            includeVectors: true);

        var queryText = queryDefinition.QueryText;
        var queryParameters = queryDefinition.GetQueryParameters();

        // Assert
        Assert.Contains("SELECT TOP 10 x.id,x.TestProperty1,x.TestProperty2,x.TestProperty3,VectorDistance(x.test_property_1, @vector) AS TestScore", queryText);
        Assert.Contains("FROM x", queryText);
        Assert.Contains("WHERE x.TestProperty2 = @cv0 AND ARRAY_CONTAINS(x.TestProperty3, @cv1)", queryText);
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

        var filter = new VectorSearchFilter().EqualTo("non-existent-property", "test-value-2");

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() =>
            AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSearchQuery<ReadOnlyMemory<float>, DummyType>(
                vector,
                keywords: null,
                this._model,
                vectorPropertyName,
                textPropertyName: null,
                ScorePropertyName,
                oldFilter: filter,
                filter: null,
                10,
                5,
                includeVectors: true));
    }

    [Fact]
    public void BuildSearchQueryWithoutFilterDoesNotContainWhereClause()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1f, 2f, 3f]);
        var vectorPropertyName = "test_property_1";

        // Act
        var queryDefinition = AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSearchQuery<ReadOnlyMemory<float>, DummyType>(
            vector,
            keywords: null,
            this._model,
            vectorPropertyName,
            textPropertyName: null,
            ScorePropertyName,
            oldFilter: null,
            filter: null,
            10,
            5,
            includeVectors: true);

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
                                         SELECT x.id,x.TestProperty1,x.TestProperty2
                                         FROM x
                                         WHERE (x.id = @rk0  AND  x.TestProperty1 = @pk0)
                                         """;

        const string KeyStoragePropertyName = "id";
        const string PartitionKeyPropertyName = "TestProperty1";

        var model = new AzureCosmosDBNoSQLVectorStoreModelBuilder().Build(
            typeof(Dictionary<string, object?>),
            new()
            {
                Properties =
                [
                    new VectorStoreRecordKeyProperty("Key", typeof(string)),
                    new VectorStoreRecordDataProperty("TestProperty1", typeof(string)),
                    new VectorStoreRecordDataProperty("TestProperty2", typeof(string))
                ]
            },
            defaultEmbeddingGenerator: null);
        var keys = new List<AzureCosmosDBNoSQLCompositeKey> { new("id", "TestProperty1") };

        // Act
        var queryDefinition = AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSelectQuery(
            model,
            KeyStoragePropertyName,
            PartitionKeyPropertyName,
            keys,
            includeVectors: true);

        var queryText = queryDefinition.QueryText;
        var queryParameters = queryDefinition.GetQueryParameters();

        // Assert
        Assert.Equal(ExpectedQueryText, queryText);

        Assert.Equal("@rk0", queryParameters[0].Name);
        Assert.Equal("id", queryParameters[0].Value);

        Assert.Equal("@pk0", queryParameters[1].Name);
        Assert.Equal("TestProperty1", queryParameters[1].Value);
    }

    [Fact]
    public void BuildSearchQueryWithHybridFieldsReturnsValidHybridQueryDefinition()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1f, 2f, 3f]);
        var keywordText = "hybrid";
        var vectorPropertyName = "TestProperty1";
        var textPropertyName = "TestProperty2";

        var filter = new VectorSearchFilter()
            .EqualTo("TestProperty2", "test-value-2")
            .AnyTagEqualTo("TestProperty3", "test-value-3");

        // Act
        var queryDefinition = AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSearchQuery<ReadOnlyMemory<float>, DummyType>(
            vector,
            [keywordText],
            this._model,
            vectorPropertyName,
            textPropertyName,
            ScorePropertyName,
            oldFilter: filter,
            filter: null,
            10,
            5,
            includeVectors: true);

        var queryText = queryDefinition.QueryText;
        var queryParameters = queryDefinition.GetQueryParameters();

        // Assert
        Assert.Contains("SELECT x.id,x.TestProperty1,x.TestProperty2,x.TestProperty3,VectorDistance(x.TestProperty1, @vector) AS TestScore", queryText);
        Assert.Contains("FROM x", queryText);
        Assert.Contains("WHERE x.TestProperty2 = @cv0 AND ARRAY_CONTAINS(x.TestProperty3, @cv1)", queryText);
        Assert.Contains("ORDER BY RANK RRF(VectorDistance(x.TestProperty1, @vector), FullTextScore(x.TestProperty2, [\"hybrid\"]))", queryText);
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

﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Xunit;

namespace SemanticKernel.Connectors.AzureCosmosDBNoSQL.UnitTests;

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
        const string ExpectedQueryText =
            "SELECT x.test_property_1,x.test_property_2,x.test_property_3,VectorDistance(x.test_property_1, @vector) AS TestScore " +
            "FROM x " +
            "WHERE x.test_property_2 = @cv0 AND ARRAY_CONTAINS(x.test_property_3, @cv1) " +
            "ORDER BY VectorDistance(x.test_property_1, @vector) " +
            "OFFSET @offset LIMIT @limit ";

        var vector = new ReadOnlyMemory<float>([1f, 2f, 3f]);
        var vectorPropertyName = "test_property_1";
        var fields = this._storagePropertyNames.Values.ToList();

        var filter = new VectorSearchFilter()
            .EqualTo("TestProperty2", "test-value-2")
            .AnyTagEqualTo("TestProperty3", "test-value-3");

        var searchOptions = new VectorSearchOptions { Filter = filter, Skip = 5, Top = 10 };

        // Act
        var queryDefinition = AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSearchQuery(
            vector,
            fields,
            this._storagePropertyNames,
            vectorPropertyName,
            ScorePropertyName,
            searchOptions);

        var queryText = queryDefinition.QueryText;
        var queryParameters = queryDefinition.GetQueryParameters();

        // Assert
        Assert.Equal(ExpectedQueryText, queryText);

        Assert.Equal("@vector", queryParameters[0].Name);
        Assert.Equal(vector, queryParameters[0].Value);

        Assert.Equal("@offset", queryParameters[1].Name);
        Assert.Equal(5, queryParameters[1].Value);

        Assert.Equal("@limit", queryParameters[2].Name);
        Assert.Equal(10, queryParameters[2].Value);

        Assert.Equal("@cv0", queryParameters[3].Name);
        Assert.Equal("test-value-2", queryParameters[3].Value);

        Assert.Equal("@cv1", queryParameters[4].Name);
        Assert.Equal("test-value-3", queryParameters[4].Value);
    }

    [Fact]
    public void BuildSearchQueryWithInvalidFilterThrowsException()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1f, 2f, 3f]);
        var vectorPropertyName = "test_property_1";
        var fields = this._storagePropertyNames.Values.ToList();

        var filter = new VectorSearchFilter().EqualTo("non-existent-property", "test-value-2");

        var searchOptions = new VectorSearchOptions { Filter = filter, Skip = 5, Top = 10 };

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() =>
            AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSearchQuery(
                vector,
                fields,
                this._storagePropertyNames,
                vectorPropertyName,
                ScorePropertyName,
                searchOptions));
    }

    [Fact]
    public void BuildSearchQueryWithoutFilterDoesNotContainWhereClause()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1f, 2f, 3f]);
        var vectorPropertyName = "test_property_1";
        var fields = this._storagePropertyNames.Values.ToList();

        var searchOptions = new VectorSearchOptions { Skip = 5, Top = 10 };

        // Act
        var queryDefinition = AzureCosmosDBNoSQLVectorStoreCollectionQueryBuilder.BuildSearchQuery(
            vector,
            fields,
            this._storagePropertyNames,
            vectorPropertyName,
            ScorePropertyName,
            searchOptions);

        var queryText = queryDefinition.QueryText;
        var queryParameters = queryDefinition.GetQueryParameters();

        // Assert
        Assert.DoesNotContain("WHERE", queryText);

        Assert.Equal("@vector", queryParameters[0].Name);
        Assert.Equal(vector, queryParameters[0].Value);

        Assert.Equal("@offset", queryParameters[1].Name);
        Assert.Equal(5, queryParameters[1].Value);

        Assert.Equal("@limit", queryParameters[2].Name);
        Assert.Equal(10, queryParameters[2].Value);
    }

    [Fact]
    public void BuildSelectQueryByDefaultReturnsValidQueryDefinition()
    {
        // Arrange
        const string ExpectedQueryText = "" +
            "SELECT x.key,x.property_1,x.property_2 " +
            "FROM x " +
            "WHERE (x.key_property = @rk0  AND  x.partition_key_property = @pk0) ";

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
}

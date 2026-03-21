// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.SemanticKernel.Connectors.CosmosNoSql;
using Xunit;

namespace SemanticKernel.Connectors.CosmosNoSql.UnitTests;

/// <summary>
/// Unit tests for <see cref="Microsoft.SemanticKernel.Connectors.CosmosNoSql.CosmosNoSqlCollectionQueryBuilder"/> class.
/// </summary>
public sealed class CosmosNoSqlCollectionQueryBuilderTests
{
    private const string ScorePropertyName = "TestScore";

    private readonly CollectionModel _model = new CosmosNoSqlModelBuilder().BuildDynamic(
        new()
        {
            Properties =
            [
                new VectorStoreKeyProperty("Key", typeof(string)),
                new VectorStoreVectorProperty("TestProperty1", typeof(ReadOnlyMemory<float>), 10) { StorageName = "test_property_1" },
                new VectorStoreDataProperty("TestProperty2", typeof(string)) { StorageName = "test_property_2" },
                new VectorStoreDataProperty("TestProperty3", typeof(string)) { StorageName = "test_property_3" }
            ]
        },
        defaultEmbeddingGenerator: null);

    [Fact]
    public void BuildSearchQueryWithoutFilterDoesNotContainWhereClause()
    {
        // Arrange
        var vector = new ReadOnlyMemory<float>([1f, 2f, 3f]);
        var vectorPropertyName = "test_property_1";

        // Act
        var queryDefinition = CosmosNoSqlCollectionQueryBuilder.BuildSearchQuery<DummyType>(
            vector,
            keywords: null,
            this._model,
            vectorPropertyName,
            distanceFunction: null,
            textPropertyName: null,
            ScorePropertyName,
            filter: null,
            scoreThreshold: null,
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

#pragma warning disable CA1812 // An internal class that is apparently never instantiated. If so, remove the code from the assembly.
    private sealed class DummyType;
#pragma warning restore CA1812
}

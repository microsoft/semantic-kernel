// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.SemanticKernel.Connectors.CosmosMongoDB;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Bson;
using Xunit;

namespace SemanticKernel.Connectors.CosmosMongoDB.UnitTests;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete

/// <summary>
/// Unit tests for <see cref="CosmosMongoCollectionSearchMapping"/> class.
/// </summary>
public sealed class CosmosMongoCollectionSearchMappingTests
{
    private readonly CollectionModel _model = new MongoModelBuilder()
        .BuildDynamic(
            new()
            {
                Properties =
                [
                    new VectorStoreKeyProperty("Property1", typeof(string)) { StorageName = "property_1" },
                    new VectorStoreDataProperty("Property2", typeof(string)) { StorageName = "property_2" }
                ]
            },
            defaultEmbeddingGenerator: null);

    [Fact]
    public void BuildFilterWithNullVectorSearchFilterReturnsNull()
    {
        // Arrange
        VectorSearchFilter? vectorSearchFilter = null;

        // Act
        var filter = CosmosMongoCollectionSearchMapping.BuildFilter(vectorSearchFilter, this._model);

        // Assert
        Assert.Null(filter);
    }

    [Fact]
    public void BuildFilterWithoutFilterClausesReturnsNull()
    {
        // Arrange
        VectorSearchFilter vectorSearchFilter = new();

        // Act
        var filter = CosmosMongoCollectionSearchMapping.BuildFilter(vectorSearchFilter, this._model);

        // Assert
        Assert.Null(filter);
    }

    [Fact]
    public void BuildFilterThrowsExceptionWithUnsupportedFilterClause()
    {
        // Arrange
        var vectorSearchFilter = new VectorSearchFilter().AnyTagEqualTo("NonExistentProperty", "TestValue");

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => CosmosMongoCollectionSearchMapping.BuildFilter(vectorSearchFilter, this._model));
    }

    [Fact]
    public void BuildFilterThrowsExceptionWithNonExistentPropertyName()
    {
        // Arrange
        var vectorSearchFilter = new VectorSearchFilter().EqualTo("NonExistentProperty", "TestValue");

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => CosmosMongoCollectionSearchMapping.BuildFilter(vectorSearchFilter, this._model));
    }

    [Fact]
    public void BuildFilterThrowsExceptionWithMultipleFilterClausesOfSameType()
    {
        // Arrange
        var vectorSearchFilter = new VectorSearchFilter()
            .EqualTo("Property1", "TestValue1")
            .EqualTo("Property1", "TestValue2");

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => CosmosMongoCollectionSearchMapping.BuildFilter(vectorSearchFilter, this._model));
    }

    [Fact]
    public void BuilderFilterByDefaultReturnsValidFilter()
    {
        // Arrange
        var expectedFilter = new BsonDocument() { ["property_1"] = new BsonDocument() { ["$eq"] = "TestValue1" } };
        var vectorSearchFilter = new VectorSearchFilter().EqualTo("Property1", "TestValue1");

        // Act
        var filter = CosmosMongoCollectionSearchMapping.BuildFilter(vectorSearchFilter, this._model);

        Assert.Equal(expectedFilter.ToJson(), filter.ToJson());
    }

    private static CollectionModel BuildModel(List<VectorStoreProperty> properties)
    => new MongoModelBuilder()
        .Build(
            typeof(Dictionary<string, object?>),
            new() { Properties = properties },
            defaultEmbeddingGenerator: null);
}

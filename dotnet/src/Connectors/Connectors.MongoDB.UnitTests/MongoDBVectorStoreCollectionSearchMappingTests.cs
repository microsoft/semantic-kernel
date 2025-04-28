// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Bson;
using Xunit;

namespace SemanticKernel.Connectors.MongoDB.UnitTests;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete

/// <summary>
/// Unit tests for <see cref="MongoDBVectorStoreCollectionSearchMapping"/> class.
/// </summary>
public sealed class MongoDBVectorStoreCollectionSearchMappingTests
{
    private readonly VectorStoreRecordModel _model = new MongoDBModelBuilder()
        .Build(
            typeof(Dictionary<string, object?>),
            new()
            {
                Properties =
                [
                    new VectorStoreRecordKeyProperty("Property1", typeof(string)) { StoragePropertyName = "property_1" },
                    new VectorStoreRecordDataProperty("Property2", typeof(string)) { StoragePropertyName = "property_2" },
                ]
            },
            defaultEmbeddingGenerator: null);

    [Fact]
    public void BuildFilterThrowsExceptionWithUnsupportedFilterClause()
    {
        // Arrange
        var vectorSearchFilter = new VectorSearchFilter().AnyTagEqualTo("NonExistentProperty", "TestValue");

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => MongoDBVectorStoreCollectionSearchMapping.BuildLegacyFilter(vectorSearchFilter, this._model));
    }

    [Fact]
    public void BuildFilterThrowsExceptionWithNonExistentPropertyName()
    {
        // Arrange
        var vectorSearchFilter = new VectorSearchFilter().EqualTo("NonExistentProperty", "TestValue");

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => MongoDBVectorStoreCollectionSearchMapping.BuildLegacyFilter(vectorSearchFilter, this._model));
    }

    [Fact]
    public void BuildFilterThrowsExceptionWithMultipleFilterClausesOfSameType()
    {
        // Arrange
        var vectorSearchFilter = new VectorSearchFilter()
            .EqualTo("Property1", "TestValue1")
            .EqualTo("Property1", "TestValue2");

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => MongoDBVectorStoreCollectionSearchMapping.BuildLegacyFilter(vectorSearchFilter, this._model));
    }

    [Fact]
    public void BuilderFilterByDefaultReturnsValidFilter()
    {
        // Arrange
        var expectedFilter = new BsonDocument() { ["property_1"] = new BsonDocument() { ["$eq"] = "TestValue1" } };
        var vectorSearchFilter = new VectorSearchFilter().EqualTo("Property1", "TestValue1");

        // Act
        var filter = MongoDBVectorStoreCollectionSearchMapping.BuildLegacyFilter(vectorSearchFilter, this._model);

        Assert.Equal(expectedFilter.ToJson(), filter.ToJson());
    }
}

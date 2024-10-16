﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;
using MongoDB.Bson;
using Xunit;

namespace SemanticKernel.Connectors.AzureCosmosDBMongoDB.UnitTests;

/// <summary>
/// Unit tests for <see cref="AzureCosmosDBMongoDBVectorStoreCollectionSearchMapping"/> class.
/// </summary>
public sealed class AzureCosmosDBMongoDBVectorStoreCollectionSearchMappingTests
{
    private readonly Dictionary<string, string> _storagePropertyNames = new()
    {
        ["Property1"] = "property_1",
        ["Property2"] = "property_2",
    };

    [Fact]
    public void BuildFilterWithNullVectorSearchFilterReturnsNull()
    {
        // Arrange
        VectorSearchFilter? vectorSearchFilter = null;

        // Act
        var filter = AzureCosmosDBMongoDBVectorStoreCollectionSearchMapping.BuildFilter(vectorSearchFilter, this._storagePropertyNames);

        // Assert
        Assert.Null(filter);
    }

    [Fact]
    public void BuildFilterWithoutFilterClausesReturnsNull()
    {
        // Arrange
        VectorSearchFilter vectorSearchFilter = new();

        // Act
        var filter = AzureCosmosDBMongoDBVectorStoreCollectionSearchMapping.BuildFilter(vectorSearchFilter, this._storagePropertyNames);

        // Assert
        Assert.Null(filter);
    }

    [Fact]
    public void BuildFilterThrowsExceptionWithUnsupportedFilterClause()
    {
        // Arrange
        var vectorSearchFilter = new VectorSearchFilter().AnyTagEqualTo("NonExistentProperty", "TestValue");

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => AzureCosmosDBMongoDBVectorStoreCollectionSearchMapping.BuildFilter(vectorSearchFilter, this._storagePropertyNames));
    }

    [Fact]
    public void BuildFilterThrowsExceptionWithNonExistentPropertyName()
    {
        // Arrange
        var vectorSearchFilter = new VectorSearchFilter().EqualTo("NonExistentProperty", "TestValue");

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => AzureCosmosDBMongoDBVectorStoreCollectionSearchMapping.BuildFilter(vectorSearchFilter, this._storagePropertyNames));
    }

    [Fact]
    public void BuildFilterThrowsExceptionWithMultipleFilterClausesOfSameType()
    {
        // Arrange
        var vectorSearchFilter = new VectorSearchFilter()
            .EqualTo("Property1", "TestValue1")
            .EqualTo("Property1", "TestValue2");

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => AzureCosmosDBMongoDBVectorStoreCollectionSearchMapping.BuildFilter(vectorSearchFilter, this._storagePropertyNames));
    }

    [Fact]
    public void BuilderFilterByDefaultReturnsValidFilter()
    {
        // Arrange
        var expectedFilter = new BsonDocument() { ["property_1"] = new BsonDocument() { ["$eq"] = "TestValue1" } };
        var vectorSearchFilter = new VectorSearchFilter().EqualTo("Property1", "TestValue1");

        // Act
        var filter = AzureCosmosDBMongoDBVectorStoreCollectionSearchMapping.BuildFilter(vectorSearchFilter, this._storagePropertyNames);

        Assert.Equal(filter.ToJson(), expectedFilter.ToJson());
    }
}

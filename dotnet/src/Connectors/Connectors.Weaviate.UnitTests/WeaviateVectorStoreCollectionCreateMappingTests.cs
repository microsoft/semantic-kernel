// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Xunit;

namespace SemanticKernel.Connectors.Weaviate.UnitTests;

/// <summary>
/// Unit tests for <see cref="WeaviateVectorStoreCollectionCreateMapping"/> class.
/// </summary>
public sealed class WeaviateVectorStoreCollectionCreateMappingTests
{
    [Fact]
    public void ItThrowsExceptionWithInvalidIndexKind()
    {
        // Arrange
        var vectorProperties = new List<VectorStoreRecordVectorProperty>
        {
            new("PropertyName", typeof(ReadOnlyMemory<float>)) { IndexKind = "non-existent-index-kind" }
        };

        var storagePropertyNames = new Dictionary<string, string> { ["PropertyName"] = "propertyName" };

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => WeaviateVectorStoreCollectionCreateMapping.MapToSchema(
            collectionName: "CollectionName",
            dataProperties: [],
            vectorProperties: vectorProperties,
            storagePropertyNames: storagePropertyNames));
    }

    [Theory]
    [InlineData(IndexKind.Hnsw, "hnsw")]
    [InlineData(IndexKind.Flat, "flat")]
    [InlineData(IndexKind.Dynamic, "dynamic")]
    public void ItReturnsCorrectSchemaWithValidIndexKind(string indexKind, string expectedIndexKind)
    {
        // Arrange
        var vectorProperties = new List<VectorStoreRecordVectorProperty>
        {
            new("PropertyName", typeof(ReadOnlyMemory<float>)) { IndexKind = indexKind }
        };

        var storagePropertyNames = new Dictionary<string, string> { ["PropertyName"] = "propertyName" };

        // Act
        var schema = WeaviateVectorStoreCollectionCreateMapping.MapToSchema(
            collectionName: "CollectionName",
            dataProperties: [],
            vectorProperties: vectorProperties,
            storagePropertyNames: storagePropertyNames);

        var actualIndexKind = schema.VectorConfigurations["propertyName"].VectorIndexType;

        // Assert
        Assert.Equal(expectedIndexKind, actualIndexKind);
    }

    [Fact]
    public void ItThrowsExceptionWithInvalidDistanceFunction()
    {
        // Arrange
        var vectorProperties = new List<VectorStoreRecordVectorProperty>
        {
            new("PropertyName", typeof(ReadOnlyMemory<float>)) { DistanceFunction = "non-existent-distance-function" }
        };

        var storagePropertyNames = new Dictionary<string, string> { ["PropertyName"] = "propertyName" };

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => WeaviateVectorStoreCollectionCreateMapping.MapToSchema(
            collectionName: "CollectionName",
            dataProperties: [],
            vectorProperties: vectorProperties,
            storagePropertyNames: storagePropertyNames));
    }

    [Theory]
    [InlineData(DistanceFunction.CosineDistance, "cosine")]
    [InlineData(DistanceFunction.NegativeDotProductSimilarity, "dot")]
    [InlineData(DistanceFunction.EuclideanSquaredDistance, "l2-squared")]
    [InlineData(DistanceFunction.Hamming, "hamming")]
    [InlineData(DistanceFunction.ManhattanDistance, "manhattan")]
    public void ItReturnsCorrectSchemaWithValidDistanceFunction(string distanceFunction, string expectedDistanceFunction)
    {
        // Arrange
        var vectorProperties = new List<VectorStoreRecordVectorProperty>
        {
            new("PropertyName", typeof(ReadOnlyMemory<float>)) { DistanceFunction = distanceFunction }
        };

        var storagePropertyNames = new Dictionary<string, string> { ["PropertyName"] = "propertyName" };

        // Act
        var schema = WeaviateVectorStoreCollectionCreateMapping.MapToSchema(
            collectionName: "CollectionName",
            dataProperties: [],
            vectorProperties: vectorProperties,
            storagePropertyNames: storagePropertyNames);

        var actualDistanceFunction = schema.VectorConfigurations["propertyName"].VectorIndexConfig?.Distance;

        // Assert
        Assert.Equal(expectedDistanceFunction, actualDistanceFunction);
    }

    [Theory]
    [InlineData(typeof(string), "text")]
    [InlineData(typeof(List<string>), "text[]")]
    [InlineData(typeof(int), "int")]
    [InlineData(typeof(int?), "int")]
    [InlineData(typeof(List<int>), "int[]")]
    [InlineData(typeof(List<int?>), "int[]")]
    [InlineData(typeof(long), "int")]
    [InlineData(typeof(long?), "int")]
    [InlineData(typeof(List<long>), "int[]")]
    [InlineData(typeof(List<long?>), "int[]")]
    [InlineData(typeof(short), "int")]
    [InlineData(typeof(short?), "int")]
    [InlineData(typeof(List<short>), "int[]")]
    [InlineData(typeof(List<short?>), "int[]")]
    [InlineData(typeof(byte), "int")]
    [InlineData(typeof(byte?), "int")]
    [InlineData(typeof(List<byte>), "int[]")]
    [InlineData(typeof(List<byte?>), "int[]")]
    [InlineData(typeof(float), "number")]
    [InlineData(typeof(float?), "number")]
    [InlineData(typeof(List<float>), "number[]")]
    [InlineData(typeof(List<float?>), "number[]")]
    [InlineData(typeof(double), "number")]
    [InlineData(typeof(double?), "number")]
    [InlineData(typeof(List<double>), "number[]")]
    [InlineData(typeof(List<double?>), "number[]")]
    [InlineData(typeof(decimal), "number")]
    [InlineData(typeof(decimal?), "number")]
    [InlineData(typeof(List<decimal>), "number[]")]
    [InlineData(typeof(List<decimal?>), "number[]")]
    [InlineData(typeof(DateTime), "date")]
    [InlineData(typeof(DateTime?), "date")]
    [InlineData(typeof(List<DateTime>), "date[]")]
    [InlineData(typeof(List<DateTime?>), "date[]")]
    [InlineData(typeof(DateTimeOffset), "date")]
    [InlineData(typeof(DateTimeOffset?), "date")]
    [InlineData(typeof(List<DateTimeOffset>), "date[]")]
    [InlineData(typeof(List<DateTimeOffset?>), "date[]")]
    [InlineData(typeof(Guid), "uuid")]
    [InlineData(typeof(Guid?), "uuid")]
    [InlineData(typeof(List<Guid>), "uuid[]")]
    [InlineData(typeof(List<Guid?>), "uuid[]")]
    [InlineData(typeof(bool), "boolean")]
    [InlineData(typeof(bool?), "boolean")]
    [InlineData(typeof(List<bool>), "boolean[]")]
    [InlineData(typeof(List<bool?>), "boolean[]")]
    [InlineData(typeof(object), "object")]
    [InlineData(typeof(List<object>), "object[]")]
    public void ItMapsPropertyCorrectly(Type propertyType, string expectedPropertyType)
    {
        // Arrange
        var dataProperties = new List<VectorStoreRecordDataProperty>
        {
            new("PropertyName", propertyType) { IsIndexed = true, IsFullTextSearchable = true }
        };

        var storagePropertyNames = new Dictionary<string, string> { ["PropertyName"] = "propertyName" };

        // Act
        var schema = WeaviateVectorStoreCollectionCreateMapping.MapToSchema(
            collectionName: "CollectionName",
            dataProperties: dataProperties,
            vectorProperties: [],
            storagePropertyNames: storagePropertyNames);

        var property = schema.Properties[0];

        // Assert
        Assert.Equal("propertyName", property.Name);
        Assert.Equal(expectedPropertyType, property.DataType[0]);
        Assert.True(property.IndexSearchable);
        Assert.True(property.IndexFilterable);
    }
}

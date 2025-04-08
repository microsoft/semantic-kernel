// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Xunit;

namespace SemanticKernel.Connectors.Weaviate.UnitTests;

/// <summary>
/// Unit tests for <see cref="WeaviateVectorStoreCollectionCreateMapping"/> class.
/// </summary>
public sealed class WeaviateVectorStoreCollectionCreateMappingTests
{
    private const bool HasNamedVectors = true;

    [Fact]
    public void ItThrowsExceptionWithInvalidIndexKind()
    {
        // Arrange
        var model = new WeaviateModelBuilder(HasNamedVectors)
            .Build(
                typeof(VectorStoreGenericDataModel<Guid>),
                new VectorStoreRecordDefinition
                {
                    Properties =
                    [
                        new VectorStoreRecordKeyProperty("Key", typeof(Guid)),
                        new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>)) { IndexKind = "non-existent-index-kind" }
                    ]
                });

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => WeaviateVectorStoreCollectionCreateMapping.MapToSchema(collectionName: "CollectionName", model));
    }

    [Theory]
    [InlineData(IndexKind.Hnsw, "hnsw")]
    [InlineData(IndexKind.Flat, "flat")]
    [InlineData(IndexKind.Dynamic, "dynamic")]
    public void ItReturnsCorrectSchemaWithValidIndexKind(string indexKind, string expectedIndexKind)
    {
        // Arrange
        var model = new WeaviateModelBuilder(HasNamedVectors)
            .Build(
                typeof(VectorStoreGenericDataModel<Guid>),
                new VectorStoreRecordDefinition
                {
                    Properties =
                    [
                        new VectorStoreRecordKeyProperty("Key", typeof(Guid)),
                        new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>)) { IndexKind = indexKind }
                    ]
                });

        // Act
        var schema = WeaviateVectorStoreCollectionCreateMapping.MapToSchema(collectionName: "CollectionName", model);
        var actualIndexKind = schema.VectorConfigurations["Vector"].VectorIndexType;

        // Assert
        Assert.Equal(expectedIndexKind, actualIndexKind);
    }

    [Fact]
    public void ItThrowsExceptionWithInvalidDistanceFunction()
    {
        // Arrange
        var model = new WeaviateModelBuilder(HasNamedVectors)
            .Build(
                typeof(VectorStoreGenericDataModel<Guid>),
                new VectorStoreRecordDefinition
                {
                    Properties =
                    [
                        new VectorStoreRecordKeyProperty("Key", typeof(Guid)),
                        new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>)) { DistanceFunction = "non-existent-distance-function" }
                    ]
                });

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => WeaviateVectorStoreCollectionCreateMapping.MapToSchema(collectionName: "CollectionName", model));
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
        var model = new WeaviateModelBuilder(HasNamedVectors)
            .Build(
                typeof(VectorStoreGenericDataModel<Guid>),
                new VectorStoreRecordDefinition
                {
                    Properties =
                    [
                        new VectorStoreRecordKeyProperty("Key", typeof(Guid)),
                        new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>)) { DistanceFunction = distanceFunction }
                    ]
                });

        // Act
        var schema = WeaviateVectorStoreCollectionCreateMapping.MapToSchema(collectionName: "CollectionName", model);

        var actualDistanceFunction = schema.VectorConfigurations["Vector"].VectorIndexConfig?.Distance;

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
    public void ItMapsPropertyCorrectly(Type propertyType, string expectedPropertyType)
    {
        // Arrange
        var model = new WeaviateModelBuilder(HasNamedVectors)
            .Build(
                typeof(VectorStoreGenericDataModel<Guid>),
                new VectorStoreRecordDefinition
                {
                    Properties =
                    [
                        new VectorStoreRecordKeyProperty("Key", typeof(Guid)),
                        new VectorStoreRecordDataProperty("PropertyName", propertyType) { IsFilterable = true, IsFullTextSearchable = true },
                        new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>))
                    ]
                },
                new JsonSerializerOptions { PropertyNamingPolicy = JsonNamingPolicy.CamelCase });

        // Act
        var schema = WeaviateVectorStoreCollectionCreateMapping.MapToSchema(collectionName: "CollectionName", model);

        var property = schema.Properties[0];

        // Assert
        Assert.Equal("propertyName", property.Name);
        Assert.Equal(expectedPropertyType, property.DataType[0]);
        Assert.True(property.IndexSearchable);
        Assert.True(property.IndexFilterable);
    }
}

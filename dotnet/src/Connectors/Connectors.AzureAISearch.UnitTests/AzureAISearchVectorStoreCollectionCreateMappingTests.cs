// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Azure.Search.Documents.Indexes.Models;
using Microsoft.SemanticKernel.Connectors.AzureAISearch;
using Microsoft.SemanticKernel.Data;
using Xunit;

namespace SemanticKernel.Connectors.AzureAISearch.UnitTests;

/// <summary>
/// Contains tests for the <see cref="AzureAISearchVectorStoreCollectionCreateMapping"/> class.
/// </summary>
public class AzureAISearchVectorStoreCollectionCreateMappingTests
{
    [Fact]
    public void MapKeyFieldCreatesSearchableField()
    {
        // Arrange
        var keyProperty = new VectorStoreRecordKeyProperty("testkey");

        // Act
        var result = AzureAISearchVectorStoreCollectionCreateMapping.MapKeyField(keyProperty);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(keyProperty.PropertyName, result.Name);
        Assert.True(result.IsKey);
        Assert.True(result.IsFilterable);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapStringDataFieldCreatesSearchableField(bool isFilterable)
    {
        // Arrange
        var dataProperty = new VectorStoreRecordDataProperty("testdata") { IsFilterable = isFilterable, PropertyType = typeof(string) };

        // Act
        var result = AzureAISearchVectorStoreCollectionCreateMapping.MapDataField(dataProperty);

        // Assert
        Assert.NotNull(result);
        Assert.IsType<SearchableField>(result);
        Assert.Equal(dataProperty.PropertyName, result.Name);
        Assert.False(result.IsKey);
        Assert.Equal(isFilterable, result.IsFilterable);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapDataFieldCreatesSimpleField(bool isFilterable)
    {
        // Arrange
        var dataProperty = new VectorStoreRecordDataProperty("testdata") { IsFilterable = isFilterable, PropertyType = typeof(int) };

        // Act
        var result = AzureAISearchVectorStoreCollectionCreateMapping.MapDataField(dataProperty);

        // Assert
        Assert.NotNull(result);
        Assert.IsType<SimpleField>(result);
        Assert.Equal(dataProperty.PropertyName, result.Name);
        Assert.Equal(SearchFieldDataType.Int32, result.Type);
        Assert.False(result.IsKey);
        Assert.Equal(isFilterable, result.IsFilterable);
    }

    [Fact]
    public void MapDataFieldFailsForNullType()
    {
        // Arrange
        var dataProperty = new VectorStoreRecordDataProperty("testdata");

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => AzureAISearchVectorStoreCollectionCreateMapping.MapDataField(dataProperty));
    }

    [Fact]
    public void MapVectorFieldCreatesVectorSearchField()
    {
        // Arrange
        var vectorProperty = new VectorStoreRecordVectorProperty("testvector") { Dimensions = 10, IndexKind = IndexKind.Flat, DistanceFunction = DistanceFunction.DotProductSimilarity };

        // Act
        var (vectorSearchField, algorithmConfiguration, vectorSearchProfile) = AzureAISearchVectorStoreCollectionCreateMapping.MapVectorField(vectorProperty);

        // Assert
        Assert.NotNull(vectorSearchField);
        Assert.NotNull(algorithmConfiguration);
        Assert.NotNull(vectorSearchProfile);
        Assert.Equal(vectorProperty.PropertyName, vectorSearchField.Name);
        Assert.Equal(vectorProperty.Dimensions, vectorSearchField.VectorSearchDimensions);

        Assert.Equal("testvectorAlgoConfig", algorithmConfiguration.Name);
        Assert.IsType<ExhaustiveKnnAlgorithmConfiguration>(algorithmConfiguration);
        var flatConfig = algorithmConfiguration as ExhaustiveKnnAlgorithmConfiguration;
        Assert.Equal(VectorSearchAlgorithmMetric.DotProduct, flatConfig!.Parameters.Metric);

        Assert.Equal("testvectorProfile", vectorSearchProfile.Name);
        Assert.Equal("testvectorAlgoConfig", vectorSearchProfile.AlgorithmConfigurationName);
    }

    [Theory]
    [InlineData(IndexKind.Hnsw, typeof(HnswAlgorithmConfiguration))]
    [InlineData(IndexKind.Flat, typeof(ExhaustiveKnnAlgorithmConfiguration))]
    public void MapVectorFieldCreatesExpectedAlgoConfigTypes(string indexKind, Type algoConfigType)
    {
        // Arrange
        var vectorProperty = new VectorStoreRecordVectorProperty("testvector") { Dimensions = 10, IndexKind = indexKind, DistanceFunction = DistanceFunction.DotProductSimilarity };

        // Act
        var (vectorSearchField, algorithmConfiguration, vectorSearchProfile) = AzureAISearchVectorStoreCollectionCreateMapping.MapVectorField(vectorProperty);

        // Assert
        Assert.Equal("testvectorAlgoConfig", algorithmConfiguration.Name);
        Assert.Equal(algoConfigType, algorithmConfiguration.GetType());
    }

    [Fact]
    public void MapVectorFieldDefaultsToHsnwAndCosine()
    {
        // Arrange
        var vectorProperty = new VectorStoreRecordVectorProperty("testvector") { Dimensions = 10 };

        // Act
        var (vectorSearchField, algorithmConfiguration, vectorSearchProfile) = AzureAISearchVectorStoreCollectionCreateMapping.MapVectorField(vectorProperty);

        // Assert
        Assert.IsType<HnswAlgorithmConfiguration>(algorithmConfiguration);
        var hnswConfig = algorithmConfiguration as HnswAlgorithmConfiguration;
        Assert.Equal(VectorSearchAlgorithmMetric.Cosine, hnswConfig!.Parameters.Metric);
    }

    [Fact]
    public void MapVectorFieldThrowsForUnsupportedDistanceFunction()
    {
        // Arrange
        var vectorProperty = new VectorStoreRecordVectorProperty("testvector") { Dimensions = 10, DistanceFunction = DistanceFunction.ManhattanDistance };

        // Act
        Assert.Throws<InvalidOperationException>(() => AzureAISearchVectorStoreCollectionCreateMapping.MapVectorField(vectorProperty));
    }

    [Fact]
    public void MapVectorFieldThrowsForMissingDimensionsCount()
    {
        // Arrange
        var vectorProperty = new VectorStoreRecordVectorProperty("testvector");

        // Act
        Assert.Throws<InvalidOperationException>(() => AzureAISearchVectorStoreCollectionCreateMapping.MapVectorField(vectorProperty));
    }

    [Theory]
    [MemberData(nameof(DataTypeMappingOptions))]
    public void GetSDKFieldDataTypeMapsTypesCorrectly(Type propertyType, SearchFieldDataType searchFieldDataType)
    {
        // Act & Assert
        Assert.Equal(searchFieldDataType, AzureAISearchVectorStoreCollectionCreateMapping.GetSDKFieldDataType(propertyType));
    }

    public static IEnumerable<object[]> DataTypeMappingOptions()
    {
        yield return new object[] { typeof(string), SearchFieldDataType.String };
        yield return new object[] { typeof(bool), SearchFieldDataType.Boolean };
        yield return new object[] { typeof(int), SearchFieldDataType.Int32 };
        yield return new object[] { typeof(long), SearchFieldDataType.Int64 };
        yield return new object[] { typeof(float), SearchFieldDataType.Double };
        yield return new object[] { typeof(double), SearchFieldDataType.Double };
        yield return new object[] { typeof(DateTime), SearchFieldDataType.DateTimeOffset };
        yield return new object[] { typeof(DateTimeOffset), SearchFieldDataType.DateTimeOffset };

        yield return new object[] { typeof(string[]), SearchFieldDataType.Collection(SearchFieldDataType.String) };
        yield return new object[] { typeof(IEnumerable<string>), SearchFieldDataType.Collection(SearchFieldDataType.String) };
        yield return new object[] { typeof(List<string>), SearchFieldDataType.Collection(SearchFieldDataType.String) };
    }
}

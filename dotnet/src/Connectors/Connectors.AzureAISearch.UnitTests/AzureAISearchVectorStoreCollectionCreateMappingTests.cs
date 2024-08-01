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
        var keyProperty = new VectorStoreRecordKeyProperty("testkey", typeof(string));
        var storagePropertyName = "test_key";

        // Act
        var result = AzureAISearchVectorStoreCollectionCreateMapping.MapKeyField(keyProperty, storagePropertyName);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(storagePropertyName, result.Name);
        Assert.True(result.IsKey);
        Assert.True(result.IsFilterable);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapFilterableStringDataFieldCreatesSimpleField(bool isFilterable)
    {
        // Arrange
        var dataProperty = new VectorStoreRecordDataProperty("testdata", typeof(string)) { IsFilterable = isFilterable };
        var storagePropertyName = "test_data";

        // Act
        var result = AzureAISearchVectorStoreCollectionCreateMapping.MapDataField(dataProperty, storagePropertyName);

        // Assert
        Assert.NotNull(result);
        Assert.IsType<SimpleField>(result);
        Assert.Equal(storagePropertyName, result.Name);
        Assert.False(result.IsKey);
        Assert.Equal(isFilterable, result.IsFilterable);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapFullTextSearchableStringDataFieldCreatesSearchableField(bool isFilterable)
    {
        // Arrange
        var dataProperty = new VectorStoreRecordDataProperty("testdata", typeof(string)) { IsFilterable = isFilterable, IsFullTextSearchable = true };
        var storagePropertyName = "test_data";

        // Act
        var result = AzureAISearchVectorStoreCollectionCreateMapping.MapDataField(dataProperty, storagePropertyName);

        // Assert
        Assert.NotNull(result);
        Assert.IsType<SearchableField>(result);
        Assert.Equal(storagePropertyName, result.Name);
        Assert.False(result.IsKey);
        Assert.Equal(isFilterable, result.IsFilterable);
    }

    [Fact]
    public void MapFullTextSearchableStringDataFieldThrowsForInvalidType()
    {
        // Arrange
        var dataProperty = new VectorStoreRecordDataProperty("testdata", typeof(int)) { IsFullTextSearchable = true };
        var storagePropertyName = "test_data";

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => AzureAISearchVectorStoreCollectionCreateMapping.MapDataField(dataProperty, storagePropertyName));
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapDataFieldCreatesSimpleField(bool isFilterable)
    {
        // Arrange
        var dataProperty = new VectorStoreRecordDataProperty("testdata", typeof(int)) { IsFilterable = isFilterable };
        var storagePropertyName = "test_data";

        // Act
        var result = AzureAISearchVectorStoreCollectionCreateMapping.MapDataField(dataProperty, storagePropertyName);

        // Assert
        Assert.NotNull(result);
        Assert.IsType<SimpleField>(result);
        Assert.Equal(storagePropertyName, result.Name);
        Assert.Equal(SearchFieldDataType.Int32, result.Type);
        Assert.False(result.IsKey);
        Assert.Equal(isFilterable, result.IsFilterable);
    }

    [Fact]
    public void MapVectorFieldCreatesVectorSearchField()
    {
        // Arrange
        var vectorProperty = new VectorStoreRecordVectorProperty("testvector", typeof(ReadOnlyMemory<float>)) { Dimensions = 10, IndexKind = IndexKind.Flat, DistanceFunction = DistanceFunction.DotProductSimilarity };
        var storagePropertyName = "test_vector";

        // Act
        var (vectorSearchField, algorithmConfiguration, vectorSearchProfile) = AzureAISearchVectorStoreCollectionCreateMapping.MapVectorField(vectorProperty, storagePropertyName);

        // Assert
        Assert.NotNull(vectorSearchField);
        Assert.NotNull(algorithmConfiguration);
        Assert.NotNull(vectorSearchProfile);
        Assert.Equal(storagePropertyName, vectorSearchField.Name);
        Assert.Equal(vectorProperty.Dimensions, vectorSearchField.VectorSearchDimensions);

        Assert.Equal("test_vectorAlgoConfig", algorithmConfiguration.Name);
        Assert.IsType<ExhaustiveKnnAlgorithmConfiguration>(algorithmConfiguration);
        var flatConfig = algorithmConfiguration as ExhaustiveKnnAlgorithmConfiguration;
        Assert.Equal(VectorSearchAlgorithmMetric.DotProduct, flatConfig!.Parameters.Metric);

        Assert.Equal("test_vectorProfile", vectorSearchProfile.Name);
        Assert.Equal("test_vectorAlgoConfig", vectorSearchProfile.AlgorithmConfigurationName);
    }

    [Theory]
    [InlineData(IndexKind.Hnsw, typeof(HnswAlgorithmConfiguration))]
    [InlineData(IndexKind.Flat, typeof(ExhaustiveKnnAlgorithmConfiguration))]
    public void MapVectorFieldCreatesExpectedAlgoConfigTypes(string indexKind, Type algoConfigType)
    {
        // Arrange
        var vectorProperty = new VectorStoreRecordVectorProperty("testvector", typeof(ReadOnlyMemory<float>)) { Dimensions = 10, IndexKind = indexKind, DistanceFunction = DistanceFunction.DotProductSimilarity };
        var storagePropertyName = "test_vector";

        // Act
        var (vectorSearchField, algorithmConfiguration, vectorSearchProfile) = AzureAISearchVectorStoreCollectionCreateMapping.MapVectorField(vectorProperty, storagePropertyName);

        // Assert
        Assert.Equal("test_vectorAlgoConfig", algorithmConfiguration.Name);
        Assert.Equal(algoConfigType, algorithmConfiguration.GetType());
    }

    [Fact]
    public void MapVectorFieldDefaultsToHsnwAndCosine()
    {
        // Arrange
        var vectorProperty = new VectorStoreRecordVectorProperty("testvector", typeof(ReadOnlyMemory<float>)) { Dimensions = 10 };
        var storagePropertyName = "test_vector";

        // Act
        var (vectorSearchField, algorithmConfiguration, vectorSearchProfile) = AzureAISearchVectorStoreCollectionCreateMapping.MapVectorField(vectorProperty, storagePropertyName);

        // Assert
        Assert.IsType<HnswAlgorithmConfiguration>(algorithmConfiguration);
        var hnswConfig = algorithmConfiguration as HnswAlgorithmConfiguration;
        Assert.Equal(VectorSearchAlgorithmMetric.Cosine, hnswConfig!.Parameters.Metric);
    }

    [Fact]
    public void MapVectorFieldThrowsForUnsupportedDistanceFunction()
    {
        // Arrange
        var vectorProperty = new VectorStoreRecordVectorProperty("testvector", typeof(ReadOnlyMemory<float>)) { Dimensions = 10, DistanceFunction = DistanceFunction.ManhattanDistance };
        var storagePropertyName = "test_vector";

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => AzureAISearchVectorStoreCollectionCreateMapping.MapVectorField(vectorProperty, storagePropertyName));
    }

    [Fact]
    public void MapVectorFieldThrowsForMissingDimensionsCount()
    {
        // Arrange
        var vectorProperty = new VectorStoreRecordVectorProperty("testvector", typeof(ReadOnlyMemory<float>));
        var storagePropertyName = "test_vector";

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => AzureAISearchVectorStoreCollectionCreateMapping.MapVectorField(vectorProperty, storagePropertyName));
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

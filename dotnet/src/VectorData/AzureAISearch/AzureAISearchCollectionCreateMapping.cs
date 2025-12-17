// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Azure.Search.Documents.Indexes.Models;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// Contains mapping helpers to use when creating a Azure AI Search vector collection.
/// </summary>
internal static class AzureAISearchCollectionCreateMapping
{
    /// <summary>
    /// Map from a <see cref="VectorStoreKeyProperty"/> to an Azure AI Search <see cref="SearchableField"/>.
    /// </summary>
    /// <param name="keyProperty">The key property definition.</param>
    /// <returns>The <see cref="SearchableField"/> for the provided property definition.</returns>
    public static SearchableField MapKeyField(KeyPropertyModel keyProperty)
    {
        return new SearchableField(keyProperty.StorageName) { IsKey = true, IsFilterable = true };
    }

    /// <summary>
    /// Map from a <see cref="VectorStoreDataProperty"/> to an Azure AI Search <see cref="SimpleField"/>.
    /// </summary>
    /// <param name="dataProperty">The data property definition.</param>
    /// <returns>The <see cref="SimpleField"/> for the provided property definition.</returns>
    /// <exception cref="InvalidOperationException">Throws when the definition is missing required information.</exception>
    public static SimpleField MapDataField(DataPropertyModel dataProperty)
    {
        if (dataProperty.IsFullTextIndexed)
        {
            if (dataProperty.Type != typeof(string))
            {
                throw new InvalidOperationException($"Property {nameof(dataProperty.IsFullTextIndexed)} on {nameof(VectorStoreDataProperty)} '{dataProperty.ModelName}' is set to true, but the property type is not a string. The Azure AI Search VectorStore supports {nameof(dataProperty.IsFullTextIndexed)} on string properties only.");
            }

            return new SearchableField(dataProperty.StorageName)
            {
                IsFilterable = dataProperty.IsIndexed,
                // Sometimes the users ask to also OrderBy given filterable property, so we make it sortable.
                IsSortable = dataProperty.IsIndexed
            };
        }

        var fieldType = AzureAISearchCollectionCreateMapping.GetSDKFieldDataType(dataProperty.Type);
        return new SimpleField(dataProperty.StorageName, fieldType)
        {
            IsFilterable = dataProperty.IsIndexed,
            // Sometimes the users ask to also OrderBy given filterable property, so we make it sortable.
            IsSortable = dataProperty.IsIndexed && !fieldType.IsCollection
        };
    }

    /// <summary>
    /// Map form a <see cref="VectorStoreVectorProperty"/> to an Azure AI Search <see cref="VectorSearchField"/> and generate the required index configuration.
    /// </summary>
    /// <param name="vectorProperty">The vector property definition.</param>
    /// <returns>The <see cref="VectorSearchField"/> and required index configuration.</returns>
    /// <exception cref="InvalidOperationException">Throws when the definition is missing required information, or unsupported options are configured.</exception>
    public static (VectorSearchField vectorSearchField, VectorSearchAlgorithmConfiguration algorithmConfiguration, VectorSearchProfile vectorSearchProfile) MapVectorField(VectorPropertyModel vectorProperty)
    {
        // Build a name for the profile and algorithm configuration based on the property name
        // since we'll just create a separate one for each vector property.
        var vectorSearchProfileName = $"{vectorProperty.StorageName}Profile";
        var algorithmConfigName = $"{vectorProperty.StorageName}AlgoConfig";

        // Read the vector index settings from the property definition and create the right index configuration.
        var indexKind = AzureAISearchCollectionCreateMapping.GetSKIndexKind(vectorProperty);
        var algorithmMetric = AzureAISearchCollectionCreateMapping.GetSDKDistanceAlgorithm(vectorProperty);

        VectorSearchAlgorithmConfiguration algorithmConfiguration = indexKind switch
        {
            IndexKind.Hnsw => new HnswAlgorithmConfiguration(algorithmConfigName) { Parameters = new HnswParameters { Metric = algorithmMetric } },
            IndexKind.Flat => new ExhaustiveKnnAlgorithmConfiguration(algorithmConfigName) { Parameters = new ExhaustiveKnnParameters { Metric = algorithmMetric } },

            _ => throw new NotSupportedException($"Index kind '{indexKind}' on {nameof(VectorStoreVectorProperty)} '{vectorProperty.ModelName}' is not supported by the Azure AI Search VectorStore.")
        };

        var vectorSearchProfile = new VectorSearchProfile(vectorSearchProfileName, algorithmConfigName);

        return (new VectorSearchField(vectorProperty.StorageName, vectorProperty.Dimensions, vectorSearchProfileName), algorithmConfiguration, vectorSearchProfile);
    }

    /// <summary>
    /// Get the configured <see cref="IndexKind"/> from the given <paramref name="vectorProperty"/>.
    /// If none is configured the default is <see cref="IndexKind.Hnsw"/>.
    /// </summary>
    /// <param name="vectorProperty">The vector property definition.</param>
    /// <returns>The configured or default <see cref="IndexKind"/>.</returns>
    public static string GetSKIndexKind(VectorPropertyModel vectorProperty)
        => vectorProperty.IndexKind ?? IndexKind.Hnsw;

    /// <summary>
    /// Get the configured <see cref="VectorSearchAlgorithmMetric"/> from the given <paramref name="vectorProperty"/>.
    /// If none is configured, the default is <see cref="VectorSearchAlgorithmMetric.Cosine"/>.
    /// </summary>
    /// <param name="vectorProperty">The vector property definition.</param>
    /// <returns>The chosen <see cref="VectorSearchAlgorithmMetric"/>.</returns>
    /// <exception cref="InvalidOperationException">Thrown if a distance function is chosen that isn't supported by Azure AI Search.</exception>
    public static VectorSearchAlgorithmMetric GetSDKDistanceAlgorithm(VectorPropertyModel vectorProperty)
        => vectorProperty.DistanceFunction switch
        {
            DistanceFunction.CosineSimilarity or null => VectorSearchAlgorithmMetric.Cosine,
            DistanceFunction.DotProductSimilarity => VectorSearchAlgorithmMetric.DotProduct,
            DistanceFunction.EuclideanDistance => VectorSearchAlgorithmMetric.Euclidean,

            _ => throw new NotSupportedException($"Distance function '{vectorProperty.DistanceFunction}' for {nameof(VectorStoreVectorProperty)} '{vectorProperty.ModelName}' is not supported by the Azure AI Search VectorStore.")
        };

    /// <summary>
    /// Maps the given property type to the corresponding <see cref="SearchFieldDataType"/>.
    /// </summary>
    /// <param name="propertyType">The property type to map.</param>
    /// <returns>The <see cref="SearchFieldDataType"/> that corresponds to the given property type.</returns>"
    /// <exception cref="InvalidOperationException">Thrown if the given type is not supported.</exception>
    public static SearchFieldDataType GetSDKFieldDataType(Type propertyType)
        => (Nullable.GetUnderlyingType(propertyType) ?? propertyType) switch
        {
            Type t when t == typeof(string) => SearchFieldDataType.String,
            Type t when t == typeof(bool) => SearchFieldDataType.Boolean,
            Type t when t == typeof(int) => SearchFieldDataType.Int32,
            Type t when t == typeof(long) => SearchFieldDataType.Int64,
            // We don't map float to SearchFieldDataType.Single, because Azure AI Search doesn't support it.
            // Half is also listed by the SDK, but currently not supported.
            Type t when t == typeof(float) => SearchFieldDataType.Double,
            Type t when t == typeof(double) => SearchFieldDataType.Double,
            Type t when t == typeof(DateTimeOffset) => SearchFieldDataType.DateTimeOffset,

            Type t when t == typeof(string[]) => SearchFieldDataType.Collection(SearchFieldDataType.String),
            Type t when t == typeof(List<string>) => SearchFieldDataType.Collection(SearchFieldDataType.String),
            Type t when t == typeof(bool[]) => SearchFieldDataType.Collection(SearchFieldDataType.Boolean),
            Type t when t == typeof(List<bool>) => SearchFieldDataType.Collection(SearchFieldDataType.Boolean),
            Type t when t == typeof(int[]) => SearchFieldDataType.Collection(SearchFieldDataType.Int32),
            Type t when t == typeof(List<int>) => SearchFieldDataType.Collection(SearchFieldDataType.Int32),
            Type t when t == typeof(long[]) => SearchFieldDataType.Collection(SearchFieldDataType.Int64),
            Type t when t == typeof(List<long>) => SearchFieldDataType.Collection(SearchFieldDataType.Int64),
            Type t when t == typeof(float[]) => SearchFieldDataType.Collection(SearchFieldDataType.Double),
            Type t when t == typeof(List<float>) => SearchFieldDataType.Collection(SearchFieldDataType.Double),
            Type t when t == typeof(double[]) => SearchFieldDataType.Collection(SearchFieldDataType.Double),
            Type t when t == typeof(List<double>) => SearchFieldDataType.Collection(SearchFieldDataType.Double),
            Type t when t == typeof(DateTimeOffset[]) => SearchFieldDataType.Collection(SearchFieldDataType.DateTimeOffset),
            Type t when t == typeof(List<DateTimeOffset>) => SearchFieldDataType.Collection(SearchFieldDataType.DateTimeOffset),

            _ => throw new NotSupportedException($"Data type '{propertyType}' for {nameof(VectorStoreDataProperty)} is not supported by the Azure AI Search VectorStore.")
        };
}

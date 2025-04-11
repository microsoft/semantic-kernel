// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using Azure.Search.Documents.Indexes.Models;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// Contains mapping helpers to use when creating a Azure AI Search vector collection.
/// </summary>
internal static class AzureAISearchVectorStoreCollectionCreateMapping
{
    /// <summary>
    /// Map from a <see cref="VectorStoreRecordKeyProperty"/> to an Azure AI Search <see cref="SearchableField"/>.
    /// </summary>
    /// <param name="keyProperty">The key property definition.</param>
    /// <returns>The <see cref="SearchableField"/> for the provided property definition.</returns>
    public static SearchableField MapKeyField(VectorStoreRecordKeyPropertyModel keyProperty)
    {
        return new SearchableField(keyProperty.StorageName) { IsKey = true, IsFilterable = true };
    }

    /// <summary>
    /// Map from a <see cref="VectorStoreRecordDataProperty"/> to an Azure AI Search <see cref="SimpleField"/>.
    /// </summary>
    /// <param name="dataProperty">The data property definition.</param>
    /// <returns>The <see cref="SimpleField"/> for the provided property definition.</returns>
    /// <exception cref="InvalidOperationException">Throws when the definition is missing required information.</exception>
    public static SimpleField MapDataField(VectorStoreRecordDataPropertyModel dataProperty)
    {
        if (dataProperty.IsFullTextIndexed)
        {
            if (dataProperty.Type != typeof(string))
            {
                throw new InvalidOperationException($"Property {nameof(dataProperty.IsFullTextIndexed)} on {nameof(VectorStoreRecordDataProperty)} '{dataProperty.ModelName}' is set to true, but the property type is not a string. The Azure AI Search VectorStore supports {nameof(dataProperty.IsFullTextIndexed)} on string properties only.");
            }

            return new SearchableField(dataProperty.StorageName)
            {
                IsFilterable = dataProperty.IsIndexed,
                // Sometimes the users ask to also OrderBy given filterable property, so we make it sortable.
                IsSortable = dataProperty.IsIndexed
            };
        }

        var fieldType = AzureAISearchVectorStoreCollectionCreateMapping.GetSDKFieldDataType(dataProperty.Type);
        return new SimpleField(dataProperty.StorageName, fieldType)
        {
            IsFilterable = dataProperty.IsIndexed,
            // Sometimes the users ask to also OrderBy given filterable property, so we make it sortable.
            IsSortable = dataProperty.IsIndexed && !fieldType.IsCollection
        };
    }

    /// <summary>
    /// Map form a <see cref="VectorStoreRecordVectorProperty"/> to an Azure AI Search <see cref="VectorSearchField"/> and generate the required index configuration.
    /// </summary>
    /// <param name="vectorProperty">The vector property definition.</param>
    /// <returns>The <see cref="VectorSearchField"/> and required index configuration.</returns>
    /// <exception cref="InvalidOperationException">Throws when the definition is missing required information, or unsupported options are configured.</exception>
    public static (VectorSearchField vectorSearchField, VectorSearchAlgorithmConfiguration algorithmConfiguration, VectorSearchProfile vectorSearchProfile) MapVectorField(VectorStoreRecordVectorPropertyModel vectorProperty)
    {
        // Build a name for the profile and algorithm configuration based on the property name
        // since we'll just create a separate one for each vector property.
        var vectorSearchProfileName = $"{vectorProperty.StorageName}Profile";
        var algorithmConfigName = $"{vectorProperty.StorageName}AlgoConfig";

        // Read the vector index settings from the property definition and create the right index configuration.
        var indexKind = AzureAISearchVectorStoreCollectionCreateMapping.GetSKIndexKind(vectorProperty);
        var algorithmMetric = AzureAISearchVectorStoreCollectionCreateMapping.GetSDKDistanceAlgorithm(vectorProperty);

        VectorSearchAlgorithmConfiguration algorithmConfiguration = indexKind switch
        {
            IndexKind.Hnsw => new HnswAlgorithmConfiguration(algorithmConfigName) { Parameters = new HnswParameters { Metric = algorithmMetric } },
            IndexKind.Flat => new ExhaustiveKnnAlgorithmConfiguration(algorithmConfigName) { Parameters = new ExhaustiveKnnParameters { Metric = algorithmMetric } },
            _ => throw new InvalidOperationException($"Index kind '{indexKind}' on {nameof(VectorStoreRecordVectorProperty)} '{vectorProperty.ModelName}' is not supported by the Azure AI Search VectorStore.")
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
    public static string GetSKIndexKind(VectorStoreRecordVectorPropertyModel vectorProperty)
        => vectorProperty.IndexKind ?? IndexKind.Hnsw;

    /// <summary>
    /// Get the configured <see cref="VectorSearchAlgorithmMetric"/> from the given <paramref name="vectorProperty"/>.
    /// If none is configured, the default is <see cref="VectorSearchAlgorithmMetric.Cosine"/>.
    /// </summary>
    /// <param name="vectorProperty">The vector property definition.</param>
    /// <returns>The chosen <see cref="VectorSearchAlgorithmMetric"/>.</returns>
    /// <exception cref="InvalidOperationException">Thrown if a distance function is chosen that isn't supported by Azure AI Search.</exception>
    public static VectorSearchAlgorithmMetric GetSDKDistanceAlgorithm(VectorStoreRecordVectorPropertyModel vectorProperty)
        => vectorProperty.DistanceFunction switch
        {
            DistanceFunction.CosineSimilarity or null => VectorSearchAlgorithmMetric.Cosine,
            DistanceFunction.DotProductSimilarity => VectorSearchAlgorithmMetric.DotProduct,
            DistanceFunction.EuclideanDistance => VectorSearchAlgorithmMetric.Euclidean,
            _ => throw new InvalidOperationException($"Distance function '{vectorProperty.DistanceFunction}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorProperty.ModelName}' is not supported by the Azure AI Search VectorStore.")
        };

    /// <summary>
    /// Maps the given property type to the corresponding <see cref="SearchFieldDataType"/>.
    /// </summary>
    /// <param name="propertyType">The property type to map.</param>
    /// <returns>The <see cref="SearchFieldDataType"/> that corresponds to the given property type.</returns>"
    /// <exception cref="InvalidOperationException">Thrown if the given type is not supported.</exception>
    public static SearchFieldDataType GetSDKFieldDataType(Type propertyType)
    {
        return propertyType switch
        {
            Type stringType when stringType == typeof(string) => SearchFieldDataType.String,
            Type boolType when boolType == typeof(bool) || boolType == typeof(bool?) => SearchFieldDataType.Boolean,
            Type intType when intType == typeof(int) || intType == typeof(int?) => SearchFieldDataType.Int32,
            Type longType when longType == typeof(long) || longType == typeof(long?) => SearchFieldDataType.Int64,
            Type floatType when floatType == typeof(float) || floatType == typeof(float?) => SearchFieldDataType.Double,
            Type doubleType when doubleType == typeof(double) || doubleType == typeof(double?) => SearchFieldDataType.Double,
            Type dateTimeType when dateTimeType == typeof(DateTime) || dateTimeType == typeof(DateTime?) => SearchFieldDataType.DateTimeOffset,
            Type dateTimeOffsetType when dateTimeOffsetType == typeof(DateTimeOffset) || dateTimeOffsetType == typeof(DateTimeOffset?) => SearchFieldDataType.DateTimeOffset,
            Type collectionType when typeof(IEnumerable).IsAssignableFrom(collectionType) => SearchFieldDataType.Collection(GetSDKFieldDataType(GetEnumerableType(propertyType))),
            _ => throw new InvalidOperationException($"Data type '{propertyType}' for {nameof(VectorStoreRecordDataProperty)} is not supported by the Azure AI Search VectorStore.")
        };
    }

    /// <summary>
    /// Gets the type of object stored in the given enumerable type.
    /// </summary>
    /// <param name="type">The enumerable to get the stored type for.</param>
    /// <returns>The type of object stored in the given enumerable type.</returns>
    /// <exception cref="InvalidOperationException">Thrown when the given type is not enumerable.</exception>
    public static Type GetEnumerableType(Type type)
    {
        if (type is IEnumerable)
        {
            return typeof(object);
        }
        else if (type.IsArray)
        {
            return type.GetElementType()!;
        }

        if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(IEnumerable<>))
        {
            return type.GetGenericArguments()[0];
        }

        if (type.GetInterfaces().FirstOrDefault(i => i.IsGenericType && i.GetGenericTypeDefinition() == typeof(IEnumerable<>)) is Type enumerableInterface)
        {
            return enumerableInterface.GetGenericArguments()[0];
        }

        throw new InvalidOperationException($"Data type '{type}' for {nameof(VectorStoreRecordDataProperty)} is not supported by the Azure AI Search VectorStore.");
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using MongoDB.Bson;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// Contains mapping helpers to use when creating a collection in Azure CosmosDB MongoDB.
/// </summary>
internal static class AzureCosmosDBMongoDBVectorStoreCollectionCreateMapping
{
    /// <summary>
    /// Returns an array of indexes to create for vector properties.
    /// </summary>
    /// <param name="vectorProperties">Collection of vector properties for index creation.</param>
    /// <param name="storagePropertyNames">A dictionary that maps from a property name to the storage name.</param>
    /// <param name="uniqueIndexes">Collection of unique existing indexes to avoid creating duplicates.</param>
    /// <param name="numLists">Number of clusters that the inverted file (IVF) index uses to group the vector data.</param>
    /// <param name="efConstruction">The size of the dynamic candidate list for constructing the graph.</param>
    public static BsonArray GetVectorIndexes(
        IReadOnlyList<VectorStoreRecordVectorProperty> vectorProperties,
        Dictionary<string, string> storagePropertyNames,
        HashSet<string?> uniqueIndexes,
        int numLists,
        int efConstruction)
    {
        var indexArray = new BsonArray();

        // Create separate index for each vector property
        foreach (var property in vectorProperties)
        {
            // Use index name same as vector property name with underscore
            var vectorPropertyName = storagePropertyNames[property.DataModelPropertyName];
            var indexName = $"{vectorPropertyName}_";

            // If index already exists, proceed to the next vector property
            if (uniqueIndexes.Contains(indexName))
            {
                continue;
            }

            // Otherwise, create a new index
            var searchOptions = new BsonDocument
            {
                { "kind", GetIndexKind(property.IndexKind, vectorPropertyName) },
                { "numLists", numLists },
                { "similarity", GetDistanceFunction(property.DistanceFunction, vectorPropertyName) },
                { "dimensions", property.Dimensions },
                { "efConstruction", efConstruction }
            };

            var indexDocument = new BsonDocument
            {
                ["name"] = indexName,
                ["key"] = new BsonDocument { [vectorPropertyName] = "cosmosSearch" },
                ["cosmosSearchOptions"] = searchOptions
            };

            indexArray.Add(indexDocument);
        }

        return indexArray;
    }

    /// <summary>
    /// Returns an array of indexes to create for filterable data properties.
    /// </summary>
    /// <param name="dataProperties">Collection of data properties for index creation.</param>
    /// <param name="storagePropertyNames">A dictionary that maps from a property name to the storage name.</param>
    /// <param name="uniqueIndexes">Collection of unique existing indexes to avoid creating duplicates.</param>
    public static BsonArray GetFilterableDataIndexes(
        IReadOnlyList<VectorStoreRecordDataProperty> dataProperties,
        Dictionary<string, string> storagePropertyNames,
        HashSet<string?> uniqueIndexes)
    {
        var indexArray = new BsonArray();

        // Create separate index for each data property
        foreach (var property in dataProperties)
        {
            if (property.IsIndexed)
            {
                // Use index name same as data property name with underscore
                var dataPropertyName = storagePropertyNames[property.DataModelPropertyName];
                var indexName = $"{dataPropertyName}_";

                // If index already exists, proceed to the next data property
                if (uniqueIndexes.Contains(indexName))
                {
                    continue;
                }

                // Otherwise, create a new index
                var indexDocument = new BsonDocument
                {
                    ["name"] = indexName,
                    ["key"] = new BsonDocument { [dataPropertyName] = 1 }
                };

                indexArray.Add(indexDocument);
            }
        }

        return indexArray;
    }

    /// <summary>
    /// More information about Azure CosmosDB for MongoDB index kinds here: <see href="https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore/vector-search" />.
    /// </summary>
    private static string GetIndexKind(string? indexKind, string vectorPropertyName)
    {
        var vectorPropertyIndexKind = AzureCosmosDBMongoDBVectorStoreCollectionSearchMapping.GetVectorPropertyIndexKind(indexKind);

        return vectorPropertyIndexKind switch
        {
            IndexKind.Hnsw => "vector-hnsw",
            IndexKind.IvfFlat => "vector-ivf",
            _ => throw new InvalidOperationException($"Index kind '{indexKind}' on {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Azure CosmosDB for MongoDB VectorStore.")
        };
    }

    /// <summary>
    /// More information about Azure CosmosDB for MongoDB distance functions here: <see href="https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore/vector-search" />.
    /// </summary>
    private static string GetDistanceFunction(string? distanceFunction, string vectorPropertyName)
    {
        var vectorPropertyDistanceFunction = AzureCosmosDBMongoDBVectorStoreCollectionSearchMapping.GetVectorPropertyDistanceFunction(distanceFunction);

        return vectorPropertyDistanceFunction switch
        {
            DistanceFunction.CosineDistance => "COS",
            DistanceFunction.DotProductSimilarity => "IP",
            DistanceFunction.EuclideanDistance => "L2",
            _ => throw new InvalidOperationException($"Distance function '{distanceFunction}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Azure CosmosDB for MongoDB VectorStore.")
        };
    }
}

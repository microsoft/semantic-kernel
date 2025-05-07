// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
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
    /// <param name="uniqueIndexes">Collection of unique existing indexes to avoid creating duplicates.</param>
    /// <param name="numLists">Number of clusters that the inverted file (IVF) index uses to group the vector data.</param>
    /// <param name="efConstruction">The size of the dynamic candidate list for constructing the graph.</param>
    public static BsonArray GetVectorIndexes(
        IReadOnlyList<VectorStoreRecordVectorPropertyModel> vectorProperties,
        HashSet<string?> uniqueIndexes,
        int numLists,
        int efConstruction)
    {
        var indexArray = new BsonArray();

        // Create separate index for each vector property
        foreach (var property in vectorProperties)
        {
            var storageName = property.StorageName;

            // Use index name same as vector property name with underscore
            var indexName = $"{storageName}_";

            // If index already exists, proceed to the next vector property
            if (uniqueIndexes.Contains(indexName))
            {
                continue;
            }

            // Otherwise, create a new index
            var searchOptions = new BsonDocument
            {
                { "kind", GetIndexKind(property.IndexKind, storageName) },
                { "numLists", numLists },
                { "similarity", GetDistanceFunction(property.DistanceFunction, storageName) },
                { "dimensions", property.Dimensions },
                { "efConstruction", efConstruction }
            };

            var indexDocument = new BsonDocument
            {
                ["name"] = indexName,
                ["key"] = new BsonDocument { [storageName] = "cosmosSearch" },
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
    /// <param name="uniqueIndexes">Collection of unique existing indexes to avoid creating duplicates.</param>
    public static BsonArray GetFilterableDataIndexes(
        IReadOnlyList<VectorStoreRecordDataPropertyModel> dataProperties,
        HashSet<string?> uniqueIndexes)
    {
        var indexArray = new BsonArray();

        // Create separate index for each data property
        foreach (var property in dataProperties)
        {
            if (property.IsIndexed)
            {
                // Use index name same as data property name with underscore
                var indexName = $"{property.StorageName}_";

                // If index already exists, proceed to the next data property
                if (uniqueIndexes.Contains(indexName))
                {
                    continue;
                }

                // Otherwise, create a new index
                var indexDocument = new BsonDocument
                {
                    ["name"] = indexName,
                    ["key"] = new BsonDocument { [property.StorageName] = 1 }
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
        => AzureCosmosDBMongoDBVectorStoreCollectionSearchMapping.GetVectorPropertyIndexKind(indexKind) switch
        {
            IndexKind.Hnsw => "vector-hnsw",
            IndexKind.IvfFlat => "vector-ivf",
            _ => throw new InvalidOperationException($"Index kind '{indexKind}' on {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Azure CosmosDB for MongoDB VectorStore.")
        };

    /// <summary>
    /// More information about Azure CosmosDB for MongoDB distance functions here: <see href="https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore/vector-search" />.
    /// </summary>
    private static string GetDistanceFunction(string? distanceFunction, string vectorPropertyName)
        => AzureCosmosDBMongoDBVectorStoreCollectionSearchMapping.GetVectorPropertyDistanceFunction(distanceFunction) switch
        {
            DistanceFunction.CosineDistance => "COS",
            DistanceFunction.DotProductSimilarity => "IP",
            DistanceFunction.EuclideanDistance => "L2",
            _ => throw new InvalidOperationException($"Distance function '{distanceFunction}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the Azure CosmosDB for MongoDB VectorStore.")
        };
}

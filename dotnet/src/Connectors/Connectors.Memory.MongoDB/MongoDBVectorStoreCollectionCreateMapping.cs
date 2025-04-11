// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using MongoDB.Bson;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// Contains mapping helpers to use when creating a collection in MongoDB.
/// </summary>
internal static class MongoDBVectorStoreCollectionCreateMapping
{
    /// <summary>
    /// Returns an array of indexes to create for vector properties.
    /// </summary>
    /// <param name="vectorProperties">Collection of vector properties for index creation.</param>
    public static BsonArray GetVectorIndexFields(IReadOnlyList<VectorStoreRecordVectorPropertyModel> vectorProperties)
    {
        var indexArray = new BsonArray();

        // Create separate index for each vector property
        foreach (var property in vectorProperties)
        {
            var indexDocument = new BsonDocument
            {
                { "type", "vector" },
                { "numDimensions", property.Dimensions },
                { "path", property.StorageName },
                { "similarity", GetDistanceFunction(property.DistanceFunction, property.ModelName) },
            };

            indexArray.Add(indexDocument);
        }

        return indexArray;
    }

    /// <summary>
    /// Returns an array of indexes to create for filterable data properties.
    /// </summary>
    /// <param name="dataProperties">Collection of data properties for index creation.</param>
    public static BsonArray GetFilterableDataIndexFields(IReadOnlyList<VectorStoreRecordDataPropertyModel> dataProperties)
    {
        var indexArray = new BsonArray();

        // Create separate index for each data property
        foreach (var property in dataProperties)
        {
            if (property.IsIndexed)
            {
                var indexDocument = new BsonDocument
                {
                    { "type", "filter" },
                    { "path", property.StorageName },
                };

                indexArray.Add(indexDocument);
            }
        }

        return indexArray;
    }

    /// <summary>
    /// Returns a list of of fields to index for full text search data properties.
    /// </summary>
    /// <param name="dataProperties">Collection of data properties for index creation.</param>
    public static List<BsonElement> GetFullTextSearchableDataIndexFields(IReadOnlyList<VectorStoreRecordDataPropertyModel> dataProperties)
    {
        var fieldElements = new List<BsonElement>();

        // Create separate index for each data property
        foreach (var property in dataProperties)
        {
            if (property.IsFullTextIndexed)
            {
                fieldElements.Add(new BsonElement(property.StorageName, new BsonArray()
                {
                    new BsonDocument() { { "type", "string" } }
                }));
            }
        }

        return fieldElements;
    }

    /// <summary>
    /// More information about MongoDB distance functions here: <see href="https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-type/#atlas-vector-search-index-fields" />.
    /// </summary>
    private static string GetDistanceFunction(string? distanceFunction, string vectorPropertyName)
        => distanceFunction switch
        {
            DistanceFunction.CosineSimilarity or null => "cosine",
            DistanceFunction.DotProductSimilarity => "dotProduct",
            DistanceFunction.EuclideanDistance => "euclidean",
            _ => throw new InvalidOperationException($"Distance function '{distanceFunction}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the MongoDB VectorStore.")
        };
}

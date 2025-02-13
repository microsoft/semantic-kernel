// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
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
    /// <param name="storagePropertyNames">A dictionary that maps from a property name to the storage name.</param>
    public static BsonArray GetVectorIndexFields(
        IReadOnlyList<VectorStoreRecordVectorProperty> vectorProperties,
        Dictionary<string, string> storagePropertyNames)
    {
        var indexArray = new BsonArray();

        // Create separate index for each vector property
        foreach (var property in vectorProperties)
        {
            // Use index name same as vector property name with underscore
            var vectorPropertyName = storagePropertyNames[property.DataModelPropertyName];

            var indexDocument = new BsonDocument
            {
                { "type", "vector" },
                { "numDimensions", property.Dimensions },
                { "path", vectorPropertyName },
                { "similarity", GetDistanceFunction(property.DistanceFunction, vectorPropertyName) },
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
    public static BsonArray GetFilterableDataIndexFields(
        IReadOnlyList<VectorStoreRecordDataProperty> dataProperties,
        Dictionary<string, string> storagePropertyNames)
    {
        var indexArray = new BsonArray();

        // Create separate index for each data property
        foreach (var property in dataProperties)
        {
            if (property.IsFilterable)
            {
                // Use index name same as data property name with underscore
                var dataPropertyName = storagePropertyNames[property.DataModelPropertyName];

                var indexDocument = new BsonDocument
                {
                    { "type", "filter" },
                    { "path", dataPropertyName },
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
    /// <param name="storagePropertyNames">A dictionary that maps from a property name to the storage name.</param>
    public static List<BsonElement> GetFullTextSearchableDataIndexFields(
        IReadOnlyList<VectorStoreRecordDataProperty> dataProperties,
        Dictionary<string, string> storagePropertyNames)
    {
        var fieldElements = new List<BsonElement>();

        // Create separate index for each data property
        foreach (var property in dataProperties)
        {
            if (property.IsFullTextSearchable)
            {
                var dataPropertyName = storagePropertyNames[property.DataModelPropertyName];

                fieldElements.Add(new BsonElement(dataPropertyName, new BsonArray()
                {
                    new BsonDocument() { { "type", "string" }, }
                }));
            }
        }

        return fieldElements;
    }

    /// <summary>
    /// More information about MongoDB distance functions here: <see href="https://www.mongodb.com/docs/atlas/atlas-vector-search/vector-search-type/#atlas-vector-search-index-fields" />.
    /// </summary>
    private static string GetDistanceFunction(string? distanceFunction, string vectorPropertyName)
    {
        var vectorPropertyDistanceFunction = MongoDBVectorStoreCollectionSearchMapping.GetVectorPropertyDistanceFunction(distanceFunction);

        return vectorPropertyDistanceFunction switch
        {
            DistanceFunction.CosineSimilarity => "cosine",
            DistanceFunction.DotProductSimilarity => "dotProduct",
            DistanceFunction.EuclideanDistance => "euclidean",
            _ => throw new InvalidOperationException($"Distance function '{distanceFunction}' for {nameof(VectorStoreRecordVectorProperty)} '{vectorPropertyName}' is not supported by the MongoDB VectorStore.")
        };
    }
}

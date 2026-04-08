// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.MongoDB;
using MongoDB.Bson;

namespace Microsoft.SemanticKernel.Connectors.CosmosMongoDB;

/// <summary>
/// Contains mapping helpers to use when searching for documents using Azure CosmosDB MongoDB.
/// </summary>
internal static class CosmosMongoCollectionSearchMapping
{
    /// <summary>Returns index kind specified on vector property or default <see cref="MongoConstants.DefaultIndexKind"/>.</summary>
    public static string GetVectorPropertyIndexKind(string? indexKind) => !string.IsNullOrWhiteSpace(indexKind) ? indexKind! : MongoConstants.DefaultIndexKind;

    /// <summary>Returns distance function specified on vector property or default <see cref="MongoConstants.DefaultDistanceFunction"/>.</summary>
    public static string GetVectorPropertyDistanceFunction(string? distanceFunction) => !string.IsNullOrWhiteSpace(distanceFunction) ? distanceFunction! : MongoConstants.DefaultDistanceFunction;

    /// <summary>Returns search part of the search query for <see cref="IndexKind.Hnsw"/> index kind.</summary>
    public static BsonDocument GetSearchQueryForHnswIndex<TVector>(
        TVector vector,
        string vectorPropertyName,
        int limit,
        int efSearch,
        BsonDocument? filter)
    {
        var searchQuery = new BsonDocument
        {
            { "vector", BsonArray.Create(vector) },
            { "path", vectorPropertyName },
            { "k", limit },
            { "efSearch", efSearch }
        };

        if (filter is not null)
        {
            searchQuery["filter"] = filter;
        }

        return new BsonDocument
        {
            { "$search",
                new BsonDocument
                {
                    { "cosmosSearch", searchQuery }
                }
            }
        };
    }

    /// <summary>Returns search part of the search query for <see cref="IndexKind.IvfFlat"/> index kind.</summary>
    public static BsonDocument GetSearchQueryForIvfIndex<TVector>(
        TVector vector,
        string vectorPropertyName,
        int limit,
        BsonDocument? filter)
    {
        var searchQuery = new BsonDocument
        {
            { "vector", BsonArray.Create(vector) },
            { "path", vectorPropertyName },
            { "k", limit },
        };

        if (filter is not null)
        {
            searchQuery["filter"] = filter;
        }

        return new BsonDocument
        {
            { "$search",
                new BsonDocument
                {
                    { "cosmosSearch", searchQuery },
                    { "returnStoredSource", true }
                }
            }
        };
    }

    /// <summary>Returns projection part of the search query to return similarity score together with document.</summary>
    public static BsonDocument GetProjectionQuery(string scorePropertyName, string documentPropertyName)
    {
        return new BsonDocument
        {
            { "$project",
                new BsonDocument
                {
                    { scorePropertyName, new BsonDocument { { "$meta", "searchScore" } } },
                    { documentPropertyName, "$$ROOT" }
                }
            }
        };
    }

    /// <summary>Returns a $match stage to filter results by score threshold.</summary>
    /// <remarks>
    /// Cosmos MongoDB returns a similarity score where higher values mean more similar,
    /// so we filter with $gte to keep results at or above the threshold.
    /// </remarks>
    public static BsonDocument GetScoreThresholdMatchQuery(string scorePropertyName, double scoreThreshold)
        => new()
        {
            {
                "$match", new BsonDocument
                {
                    { scorePropertyName, new BsonDocument { { "$gte", scoreThreshold } } }
                }
            }
        };
}

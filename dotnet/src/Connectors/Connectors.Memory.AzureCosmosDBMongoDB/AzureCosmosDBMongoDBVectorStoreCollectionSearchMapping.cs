// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Data;
using MongoDB.Bson;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// Contains mapping helpers to use when searching for documents using Azure CosmosDB MongoDB.
/// </summary>
internal static class AzureCosmosDBMongoDBVectorStoreCollectionSearchMapping
{
    /// <summary>Returns search part of the search query for <see cref="IndexKind.Hnsw"/> index kind.</summary>
    public static BsonDocument GetSearchQueryForHnswIndex<TVector>(
        TVector vector,
        string vectorPropertyName,
        int limit,
        int efSearch)
    {
        return new BsonDocument
        {
            { "$search",
                new BsonDocument
                {
                    { "cosmosSearch",
                        new BsonDocument
                        {
                            { "vector", BsonArray.Create(vector) },
                            { "path", vectorPropertyName },
                            { "k", limit },
                            { "efSearch", efSearch }
                        }
                    }
                }
            }
        };
    }

    /// <summary>Returns search part of the search query for <see cref="IndexKind.IvfFlat"/> index kind.</summary>
    public static BsonDocument GetSearchQueryForIvfIndex<TVector>(
        TVector vector,
        string vectorPropertyName,
        int limit)
    {
        return new BsonDocument
        {
            { "$search",
                new BsonDocument
                {
                    { "cosmosSearch",
                        new BsonDocument
                        {
                            { "vector", BsonArray.Create(vector) },
                            { "path", vectorPropertyName },
                            { "k", limit },
                        }
                    },
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
}

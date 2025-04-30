// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using MongoDB.Bson;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// Contains mapping helpers to use when searching for documents using MongoDB.
/// </summary>
internal static class MongoDBVectorStoreCollectionSearchMapping
{
#pragma warning disable CS0618 // VectorSearchFilter is obsolete
    /// <summary>
    /// Build MongoDB filter from the provided <see cref="VectorSearchFilter"/>.
    /// </summary>
    /// <param name="vectorSearchFilter">The <see cref="VectorSearchFilter"/> to build MongoDB filter from.</param>
    /// <param name="model">The model.</param>
    /// <exception cref="NotSupportedException">Thrown when the provided filter type is unsupported.</exception>
    /// <exception cref="InvalidOperationException">Thrown when property name specified in filter doesn't exist.</exception>
    public static BsonDocument? BuildLegacyFilter(
        VectorSearchFilter vectorSearchFilter,
        VectorStoreRecordModel model)
    {
        const string EqualOperator = "$eq";

        var filterClauses = vectorSearchFilter.FilterClauses.ToList();

        if (filterClauses is not { Count: > 0 })
        {
            return null;
        }

        var filter = new BsonDocument();

        foreach (var filterClause in filterClauses)
        {
            string propertyName;
            BsonValue propertyValue;
            string filterOperator;

            if (filterClause is EqualToFilterClause equalToFilterClause)
            {
                propertyName = equalToFilterClause.FieldName;
                propertyValue = BsonValue.Create(equalToFilterClause.Value);
                filterOperator = EqualOperator;
            }
            else
            {
                throw new NotSupportedException(
                    $"Unsupported filter clause type '{filterClause.GetType().Name}'. " +
                    $"Supported filter clause types are: {string.Join(", ", [
                        nameof(EqualToFilterClause)])}");
            }

            if (!model.PropertyMap.TryGetValue(propertyName, out var property))
            {
                throw new InvalidOperationException($"Property name '{propertyName}' provided as part of the filter clause is not a valid property name.");
            }

            if (filter.Contains(property.StorageName))
            {
                if (filter[property.StorageName] is BsonDocument document && document.Contains(filterOperator))
                {
                    throw new NotSupportedException(
                        $"Filter with operator '{filterOperator}' is already added to '{propertyName}' property. " +
                        "Multiple filters of the same type in the same property are not supported.");
                }

                filter[property.StorageName][filterOperator] = propertyValue;
            }
            else
            {
                filter[property.StorageName] = new BsonDocument() { [filterOperator] = propertyValue };
            }
        }

        return filter;
    }
#pragma warning restore CS0618

    /// <summary>Returns search part of the search query.</summary>
    public static BsonDocument GetSearchQuery<TVector>(
        TVector vector,
        string indexName,
        string vectorPropertyName,
        int limit,
        int numCandidates,
        BsonDocument? filter)
    {
        var searchQuery = new BsonDocument
        {
            { "index", indexName },
            { "queryVector", BsonArray.Create(vector) },
            { "path", vectorPropertyName },
            { "limit", limit },
            { "numCandidates", numCandidates },
        };

        if (filter is not null)
        {
            searchQuery["filter"] = filter;
        }

        return new BsonDocument
        {
            { "$vectorSearch", searchQuery }
        };
    }

    /// <summary>Returns projection part of the search query to return similarity score together with document.</summary>
    public static BsonDocument GetProjectionQuery(string scorePropertyName, string documentPropertyName)
    {
        return new BsonDocument
        {
            {
                "$project", new BsonDocument
                {
                    { scorePropertyName, new BsonDocument { { "$meta", "vectorSearchScore" } } },
                    { documentPropertyName, "$$ROOT" }
                }
            }
        };
    }

    /// <summary>Returns a pipeline for hybrid search using vector search and full text search.</summary>
    public static BsonDocument[] GetHybridSearchPipeline<TVector>(
        TVector vector,
        ICollection<string> keywords,
        string collectionName,
        string vectorIndexName,
        string fullTextSearchIndexName,
        string vectorPropertyName,
        string textPropertyName,
        string scorePropertyName,
        string documentPropertyName,
        int limit,
        int numCandidates,
        BsonDocument? filter)
    {
        // Create the FullTextSearch pipeline first.
        var ftsPipeline = new List<BsonDocument>
        {
            // The full text search stage.
            GetFullTextSearchQuery(keywords, fullTextSearchIndexName, textPropertyName, filter),
            // Limit the results to the maximum that we may require.
            new()
            {
                {
                    "$limit", limit
                }
            },
            // Converts the list of documents to a single document with an array property containing all the source documents.
            GroupDocsSection(),
            // Creates separate documents again where each has a new rank property based on the index of the document.
            UnwindDocsArraySection(),
            // Add a weighted score based on the rank of the document.
            AddScore("fts_score", 0.9),
            // Project the score, the id and the original document as properties, so that we can join with the vector search results on id.
            ProjectWithScore("fts_score"),
        };

        // Add filtering to the FullTextSearch pipeline if filter is provided.
        if (filter is not null)
        {
            // Insert filter at the second position, since
            // MongoDB requires search to be the first stage.
            ftsPipeline.Insert(1, new BsonDocument
            {
                {
                    "$match", filter
                }
            });
        }

        // Create combined pipeline with the vector search part first.
        var pipeline = new BsonDocument[]
        {
            // The vector search stage.
            GetSearchQuery(vector, vectorIndexName, vectorPropertyName, limit, numCandidates, filter),
            // Converts the list of documents to a single document with an array property containing all the source documents.
            GroupDocsSection(),
            // Creates separate documents again where each has a new rank property based on the index of the document.
            UnwindDocsArraySection(),
            // Add a weighted score based on the rank of the document.
            AddScore("vs_score", 0.1),
            // Project the score, the id and the original document as properties, so that we can join with the vector search results on id.
            ProjectWithScore("vs_score"),
            // Union the vector search results with the results from the full text search pipeilne.
            new()
            {
                {
                    "$unionWith", new BsonDocument
                    {
                        { "coll", collectionName },
                        { "pipeline", new BsonArray(ftsPipeline) }
                    }
                }
            },
            // Group by id and store scores from each pipeline, so that we don't have duplicate documents.
            new()
            {
                {
                    "$group", new BsonDocument
                    {
                        { "_id", "$_id" },
                        { "docs", new BsonDocument { { "$first", "$docs" } } },
                        { "vs_score", new BsonDocument { { "$max", "$vs_score" } } },
                        { "fts_score", new BsonDocument { { "$max", "$fts_score" } } }
                    }
                }
            },
            // If a score is missing (i.e. the document was only found in the other pipeline), default the missing score to 0.
            new()
            {
                {
                    "$project", new BsonDocument
                    {
                        { "_id", 1 },
                        { "docs", 1 },
                        { "vs_score", new BsonDocument { { "$ifNull", new BsonArray { "$vs_score", 0 } } } },
                        { "fts_score", new BsonDocument { { "$ifNull", new BsonArray { "$fts_score", 0 } } } }
                    }
                }
            },
            // Calculate a combined score based on the vector search and full text search scores.
            new()
            {
                {
                    "$project", new BsonDocument
                    {
                        { scorePropertyName, new BsonDocument { { "$add", new BsonArray { "$fts_score", "$vs_score" } } } },
                        { "vs_score", 1 },
                        { "fts_score", 1 },
                        { documentPropertyName, "$docs" }
                    }
                }
            },
            // Sort by score desc.
            new()
            {
                {
                    "$sort", new BsonDocument
                    {
                        { scorePropertyName, -1 }
                    }
                }
            },
            // Take the required N results.
            new()
            {
                {
                    "$limit", limit
                }
            },
        };

        return pipeline;
    }

    /// <summary>Builds the full text search query stage.</summary>
    private static BsonDocument GetFullTextSearchQuery(
        ICollection<string> keywords,
        string fullTextSearchIndexName,
        string textPropertyName,
        BsonDocument? filter)
    {
        var fullTextSearchQuery = new BsonDocument
        {
            {
                "$search", new BsonDocument
                {
                    { "index", fullTextSearchIndexName },
                    { "text",
                        new BsonDocument
                        {
                            { "query", new BsonArray(keywords) },
                            { "path", textPropertyName },
                            { "matchCriteria", "any" }
                        }
                    }
                }
            }
        };

        return fullTextSearchQuery;
    }

    /// <summary>Create a stage that groups all documents into a single document with an array property containing all the source documents.</summary>
    private static BsonDocument GroupDocsSection()
    {
        return new BsonDocument
        {
            {
                "$group", new BsonDocument
                {
                    { "_id", BsonNull.Value },
                    { "docs", new BsonDocument { { "$push", "$$ROOT" } } }
                }
            }
        };
    }

    /// <summary>Creates a stage that splits an array of documents from a single document into separate documents and adds an index property for each document based on its index in the array.</summary>
    private static BsonDocument UnwindDocsArraySection()
    {
        return new BsonDocument
        {
            {
                "$unwind", new BsonDocument
                {
                    { "path", "$docs" },
                    { "includeArrayIndex", "rank" }
                }
            }
        };
    }

    /// <summary>Adds a weighted score to each document based on the rank property on the document.</summary>
    private static BsonDocument AddScore(string scoreName, double weight)
    {
        return new()
        {
            {
                "$addFields", new BsonDocument
                {
                    {
                        scoreName, new BsonDocument
                        {
                            {
                                "$multiply", new BsonArray()
                                {
                                    weight,
                                    new BsonDocument
                                    {
                                        { "$divide", new BsonArray()
                                            {
                                                1.0,
                                                new BsonDocument
                                                {
                                                    { "$add", new BsonArray()
                                                        {
                                                            "$rank",
                                                            60
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                }
            }
        };
    }

    /// <summary>Projects the score, the id and the original document as properties.</summary>
    private static BsonDocument ProjectWithScore(string scoreName)
    {
        return new()
        {
            {
                "$project", new BsonDocument
                {
                    { scoreName, 1 },
                    { "_id", "$docs._id" },
                    { "docs", "$docs" }
                }
            }
        };
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Linq.Expressions;
using System.Text.Json;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Contains methods to build Weaviate queries.
/// </summary>
internal static class WeaviateQueryBuilder
{
    /// <summary>
    /// Builds Weaviate search query.
    /// More information here: <see href="https://weaviate.io/developers/weaviate/api/graphql/get"/>.
    /// </summary>
    public static string BuildSearchQuery<TRecord, TVector>(
        TVector vector,
        string collectionName,
        string vectorPropertyName,
        JsonSerializerOptions jsonSerializerOptions,
        int top,
        VectorSearchOptions<TRecord> searchOptions,
        CollectionModel model,
        bool hasNamedVectors)
    {
        var vectorsQuery = GetVectorsPropertyQuery(searchOptions.IncludeVectors, hasNamedVectors, model);

        var filter = searchOptions.Filter is not null
            ? new WeaviateFilterTranslator().Translate(searchOptions.Filter, model)
            : null;

        var vectorArray = JsonSerializer.Serialize(vector, jsonSerializerOptions);

        // Weaviate nearVector supports distance parameter for thresholding.
        // Distance works for all distance functions (lower values = more similar).
        var distanceFilter = searchOptions.ScoreThreshold.HasValue
            ? $"distance: {searchOptions.ScoreThreshold.Value}"
            : string.Empty;

        return $$"""
        {
          Get {
            {{collectionName}} (
              limit: {{top}}
              offset: {{searchOptions.Skip}}
              {{(filter is null ? "" : "where: " + filter)}}
              nearVector: {
                {{GetTargetVectorsQuery(hasNamedVectors, vectorPropertyName)}}
                vector: {{vectorArray}}
                {{distanceFilter}}
              }
            ) {
              {{string.Join(" ", model.DataProperties.Select(p => p.StorageName))}}
              {{WeaviateConstants.AdditionalPropertiesPropertyName}} {
                {{WeaviateConstants.ReservedKeyPropertyName}}
                {{WeaviateConstants.ScorePropertyName}}
                {{vectorsQuery}}
              }
            }
          }
        }
        """;
    }

    /// <summary>
    /// Builds Weaviate search query.
    /// More information here: <see href="https://weaviate.io/developers/weaviate/api/graphql/get"/>.
    /// </summary>
    public static string BuildQuery<TRecord>(
        Expression<Func<TRecord, bool>> filter,
        int top,
        FilteredRecordRetrievalOptions<TRecord> queryOptions,
        string collectionName,
        CollectionModel model,
        bool hasNamedVectors)
    {
        var vectorsQuery = GetVectorsPropertyQuery(queryOptions.IncludeVectors, hasNamedVectors, model);

        var orderBy = queryOptions.OrderBy?.Invoke(new()).Values;
        var sortPaths = orderBy is not { Count: > 0 } ? "" : string.Join(",", orderBy.Select(sortInfo =>
        {
            string sortPath = model.GetDataOrKeyProperty(sortInfo.PropertySelector).StorageName;

            return $$"""{ path: ["{{JsonEncodedText.Encode(sortPath)}}"], order: {{(sortInfo.Ascending ? "asc" : "desc")}} }""";
        }));

        var translatedFilter = new WeaviateFilterTranslator().Translate(filter, model);

        return $$"""
        {
          Get {
            {{collectionName}} (
              limit: {{top}}
              offset: {{queryOptions.Skip}}
              {{(translatedFilter is null ? "" : "where: " + translatedFilter)}}
              sort: [ {{sortPaths}} ]
            ) {
              {{string.Join(" ", model.DataProperties.Select(p => p.StorageName))}}
              {{WeaviateConstants.AdditionalPropertiesPropertyName}} {
                {{WeaviateConstants.ReservedKeyPropertyName}}
                {{WeaviateConstants.ScorePropertyName}}
                {{vectorsQuery}}
              }
            }
          }
        }
        """;
    }

    /// <summary>
    /// Builds Weaviate hybrid search query.
    /// More information here: <see href="https://weaviate.io/developers/weaviate/api/graphql/get"/>.
    /// </summary>
    public static string BuildHybridSearchQuery<TRecord, TVector>(
        TVector vector,
        int top,
        string keywords,
        string collectionName,
        CollectionModel model,
        IVectorPropertyModel vectorProperty,
        IDataPropertyModel textProperty,
        JsonSerializerOptions jsonSerializerOptions,
        HybridSearchOptions<TRecord> searchOptions,
        bool hasNamedVectors)
    {
        // https://docs.weaviate.io/weaviate/api/graphql/search-operators#hybrid
        var vectorsQuery = GetVectorsPropertyQuery(searchOptions.IncludeVectors, hasNamedVectors, model);

        var filter = searchOptions.Filter is not null
            ? new WeaviateFilterTranslator().Translate(searchOptions.Filter, model)
            : null;

        var vectorArray = JsonSerializer.Serialize(vector, jsonSerializerOptions);
        var sanitizedKeywords = keywords.Replace("\\", "\\\\").Replace("\"", "\\\"");

        return $$"""
        {
          Get {
            {{collectionName}} (
              limit: {{top}}
              offset: {{searchOptions.Skip}}
              {{(filter is null ? "" : "where: " + filter)}}
              hybrid: {
                query: "{{sanitizedKeywords}}"
                properties: ["{{textProperty.StorageName}}"]
                {{GetTargetVectorsQuery(hasNamedVectors, vectorProperty.StorageName)}}
                vector: {{vectorArray}}
                fusionType: rankedFusion
              }
            ) {
              {{string.Join(" ", model.DataProperties.Select(p => p.StorageName))}}
              {{WeaviateConstants.AdditionalPropertiesPropertyName}} {
                {{WeaviateConstants.ReservedKeyPropertyName}}
                {{WeaviateConstants.HybridScorePropertyName}}
                {{vectorsQuery}}
              }
            }
          }
        }
        """;
    }

    #region private

    private static string GetTargetVectorsQuery(bool hasNamedVectors, string vectorPropertyName)
    {
        return hasNamedVectors ? $"targetVectors: [\"{vectorPropertyName}\"]" : string.Empty;
    }

    private static string GetVectorsPropertyQuery(
        bool includeVectors,
        bool hasNamedVectors,
        CollectionModel model)
    {
        return includeVectors
            ? hasNamedVectors
                ? $"vectors {{ {string.Join(" ", model.VectorProperties.Select(p => p.StorageName))} }}"
                : WeaviateConstants.ReservedSingleVectorPropertyName
            : string.Empty;
    }

    #endregion
}

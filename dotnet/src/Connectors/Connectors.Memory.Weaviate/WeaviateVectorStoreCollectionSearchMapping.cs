// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using System.Text.Json.Nodes;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Contains methods to perform Weaviate vector search data mapping.
/// </summary>
internal static class WeaviateVectorStoreCollectionSearchMapping
{
    /// <summary>
    /// Maps vector search result to the format, which is processable by <see cref="WeaviateVectorStoreRecordMapper{TRecord}"/>.
    /// </summary>
    public static (JsonObject StorageModel, double? Score) MapSearchResult(
        JsonNode result,
        string scorePropertyName,
        bool hasNamedVectors)
    {
        var additionalProperties = result[WeaviateConstants.AdditionalPropertiesPropertyName];

        var scoreProperty = additionalProperties?[scorePropertyName];
        double? score = scoreProperty?.GetValueKind() switch
        {
            JsonValueKind.Number => scoreProperty.GetValue<double>(),
            JsonValueKind.String => double.Parse(scoreProperty.GetValue<string>()),
            _ => null
        };

        var vectorPropertyName = hasNamedVectors ?
            WeaviateConstants.ReservedVectorPropertyName :
            WeaviateConstants.ReservedSingleVectorPropertyName;

        var id = additionalProperties?[WeaviateConstants.ReservedKeyPropertyName];
        var vectors = additionalProperties?[vectorPropertyName];

        var storageModel = new JsonObject
        {
            { WeaviateConstants.ReservedKeyPropertyName, id?.DeepClone() },
            { WeaviateConstants.ReservedDataPropertyName, result?.DeepClone() },
            { vectorPropertyName, vectors?.DeepClone() },
        };

        return (storageModel, score);
    }
}

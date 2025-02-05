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
    public static (JsonObject StorageModel, double? Score) MapSearchResult(JsonNode result, string scorePropertyName)
    {
        var additionalProperties = result[WeaviateConstants.AdditionalPropertiesPropertyName];

        var scoreProperty = additionalProperties?[scorePropertyName];
        double? score = scoreProperty?.GetValueKind() switch
        {
            JsonValueKind.Number => scoreProperty.GetValue<double>(),
            JsonValueKind.String => double.Parse(scoreProperty.GetValue<string>()),
            _ => null
        };

        var id = additionalProperties?[WeaviateConstants.ReservedKeyPropertyName];
        var vectors = additionalProperties?[WeaviateConstants.ReservedVectorPropertyName];

        var storageModel = new JsonObject
        {
            { WeaviateConstants.ReservedKeyPropertyName, id?.DeepClone() },
            { WeaviateConstants.ReservedDataPropertyName, result?.DeepClone() },
            { WeaviateConstants.ReservedVectorPropertyName, vectors?.DeepClone() },
        };

        return (storageModel, score);
    }
}

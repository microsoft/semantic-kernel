// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

// ReSharper disable InconsistentNaming
namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// Similarity metric to use with the index. Possible options are COS (cosine distance), L2 (Euclidean distance), and IP (inner product).
/// </summary>
public enum AzureCosmosDBSimilarityType
{
    /// <summary>
    /// Cosine similarity
    /// </summary>
    [JsonPropertyName("COS")]
    Cosine,

    /// <summary>
    /// Inner Product similarity
    /// </summary>
    [JsonPropertyName("IP")]
    InnerProduct,

    /// <summary>
    /// Euclidean similarity
    /// </summary>
    [JsonPropertyName("L2")]
    Euclidean
}

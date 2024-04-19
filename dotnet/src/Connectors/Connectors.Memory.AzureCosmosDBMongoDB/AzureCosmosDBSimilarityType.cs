// Copyright (c) Microsoft. All rights reserved.

using Newtonsoft.Json;

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
    [JsonProperty("COS")]
    Cosine,

    /// <summary>
    /// Inner Product similarity
    /// </summary>
    [JsonProperty("IP")]
    InnerProduct,

    /// <summary>
    /// Eucledian similarity
    /// </summary>
    [JsonProperty("L2")]
    Eucledian
}

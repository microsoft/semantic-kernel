// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

// ReSharper disable InconsistentNaming
namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// Type of vector index to create. The options are vector-ivf and vector-hnsw.
/// </summary>
public enum AzureCosmosDBVectorSearchType
{
    /// <summary>
    /// vector-ivf is available on all cluster tiers
    /// </summary>
    [JsonPropertyName("vector_ivf")]
    VectorIVF,

    /// <summary>
    /// vector-hnsw is available on M40 cluster tiers and higher.
    /// </summary>
    [JsonPropertyName("vector_hnsw")]
    VectorHNSW
}

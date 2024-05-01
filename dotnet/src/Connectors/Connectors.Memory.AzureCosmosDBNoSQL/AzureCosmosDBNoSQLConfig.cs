// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Azure.Cosmos;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// Get more details about Azure Cosmos DB and these configs https://learn.microsoft.com/azure/cosmos-db/
/// </summary>
public class AzureCosmosDBNoSQLConfig
{
    /// <summary>
    /// Application name for the client for tracking and logging
    /// </summary>
    public string ApplicationName { get; set; }

    /// <summary>
    /// Kind: Type of vector index to create.
    ///     Possible options are:
    ///         - vector-ivf
    ///         - vector-hnsw: available as a preview feature only,
    ///                        to enable visit https://learn.microsoft.com/azure/azure-resource-manager/management/preview-features
    /// </summary>
    public VectorIndexType Kind { get; set; }

    /// <summary>
    /// Number of dimensions for vector similarity. The maximum number of supported dimensions is 2000.
    /// </summary>
    public int Dimensions { get; set; }

    /// <summary>
    /// Similarity: Distance function to use for the index.
    /// </summary>
    public DistanceFunction DistanceFunction { get; set; }

    /// <summary>
    /// Initialize the AzureCosmosDBNoSQLConfig with default values
    /// </summary>
    public AzureCosmosDBNoSQLConfig()
    {
        this.ApplicationName = HttpHeaderConstant.Values.UserAgent;
        this.Kind = VectorIndexType.QuantizedFlat;
        this.DistanceFunction = DistanceFunction.Cosine;
    }
}

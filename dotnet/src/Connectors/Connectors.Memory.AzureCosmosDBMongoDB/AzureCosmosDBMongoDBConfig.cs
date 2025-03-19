// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// Azure Cosmos Mongo vCore configuration.
/// More information here: https://learn.microsoft.com/azure/cosmos-db/mongodb/vcore/vector-search.
/// </summary>
/// <remarks>
/// Initialize the <see cref="AzureCosmosDBMongoDBConfig"/> with default values.
/// </remarks>
[Obsolete("The IMemoryStore abstraction is being phased out, use Microsoft.Extensions.VectorData and AzureMongoDBMongoDBVectorStore")]
public class AzureCosmosDBMongoDBConfig(int dimensions)
{
    private const string DefaultIndexName = "default_index";

    /// <summary>
    /// Application name for the client for tracking and logging
    /// </summary>
    public string ApplicationName { get; set; } = HttpHeaderConstant.Values.UserAgent;

    /// <summary>
    /// Index name for the Mongo vCore DB. Default is "default_index".
    /// </summary>
    public string IndexName { get; set; } = DefaultIndexName;

    /// <summary>
    /// Type of vector index to create.
    ///     Possible options are:
    ///         - vector-ivf (default)
    ///         - vector-hnsw: available as a preview feature only,
    ///                        to enable visit https://learn.microsoft.com/azure/azure-resource-manager/management/preview-features
    /// </summary>
    public AzureCosmosDBVectorSearchType Kind { get; set; } = AzureCosmosDBVectorSearchType.VectorIVF;

    /// <summary>
    /// This integer is the number of clusters that the inverted file (IVF) index uses to group the vector data. Default is 1.
    /// We recommend that numLists is set to documentCount/1000 for up to 1 million documents and to sqrt(documentCount)
    /// for more than 1 million documents. Using a numLists value of 1 is akin to performing brute-force search, which has
    /// limited performance.
    /// </summary>
    public int NumLists { get; set; } = 1;

    /// <summary>
    /// Number of dimensions for vector similarity. The maximum number of supported dimensions is 2000.
    /// </summary>
    public int Dimensions { get; set; } = dimensions;

    /// <summary>
    /// Similarity metric to use with the IVF index.
    ///     Possible options are:
    ///         - COS (cosine distance, default),
    ///         - L2 (Euclidean distance), and
    ///         - IP (inner product).
    /// </summary>
    public AzureCosmosDBSimilarityType Similarity { get; set; } = AzureCosmosDBSimilarityType.Cosine;

    /// <summary>
    /// The max number of connections per layer (16 by default, minimum value is 2, maximum value is
    /// 100). Higher m is suitable for datasets with high dimensionality and/or high accuracy requirements.
    /// </summary>
    public int NumberOfConnections { get; set; } = 16;

    /// <summary>
    /// The size of the dynamic candidate list for constructing the graph (64 by default, minimum value is 4,
    /// maximum value is 1000). Higher ef_construction will result in better index quality and higher accuracy, but it will
    /// also increase the time required to build the index. EfConstruction has to be at least 2 * m
    /// </summary>
    public int EfConstruction { get; set; } = 64;

    /// <summary>
    /// The size of the dynamic candidate list for search (40 by default). A higher value provides better recall at
    /// the cost of speed.
    /// </summary>
    public int EfSearch { get; set; } = 40;
}

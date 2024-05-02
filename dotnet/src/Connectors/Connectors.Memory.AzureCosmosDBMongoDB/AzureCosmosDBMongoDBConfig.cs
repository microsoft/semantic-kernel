// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// Get more details about Azure Cosmos Mongo vCore and these configs https://learn.microsoft.com/azure/cosmos-db/mongodb/vcore/vector-search
/// </summary>
public class AzureCosmosDBMongoDBConfig
{
    /// <summary>
    /// Application name for the client for tracking and logging
    /// </summary>
    public string ApplicationName { get; set; }

    /// <summary>
    /// Index name for the Mongo vCore DB
    /// </summary>
    public string IndexName { get; set; }

    /// <summary>
    /// Kind: Type of vector index to create.
    ///     Possible options are:
    ///         - vector-ivf
    ///         - vector-hnsw: available as a preview feature only,
    ///                        to enable visit https://learn.microsoft.com/azure/azure-resource-manager/management/preview-features
    /// </summary>
    public AzureCosmosDBVectorSearchType Kind { get; set; }

    /// <summary>
    /// NumLists: This integer is the number of clusters that the inverted file (IVF) index uses to group the vector data.
    /// We recommend that numLists is set to documentCount/1000 for up to 1 million documents and to sqrt(documentCount)
    /// for more than 1 million documents. Using a numLists value of 1 is akin to performing brute-force search, which has
    /// limited performance.
    /// </summary>
    public int NumLists { get; set; }

    /// <summary>
    /// Number of dimensions for vector similarity. The maximum number of supported dimensions is 2000.
    /// </summary>
    public int Dimensions { get; set; }

    /// <summary>
    /// Similarity: Similarity metric to use with the IVF index.
    ///     Possible options are:
    ///         - COS (cosine distance),
    ///         - L2 (Euclidean distance), and
    ///         - IP (inner product).
    /// </summary>
    public AzureCosmosDBSimilarityType Similarity { get; set; }

    /// <summary>
    /// NumberOfConnections: The max number of connections per layer (16 by default, minimum value is 2, maximum value is
    /// 100). Higher m is suitable for datasets with high dimensionality and/or high accuracy requirements.
    /// </summary>
    public int NumberOfConnections { get; set; }

    /// <summary>
    /// EfConstruction: the size of the dynamic candidate list for constructing the graph (64 by default, minimum value is 4,
    /// maximum value is 1000). Higher ef_construction will result in better index quality and higher accuracy, but it will
    /// also increase the time required to build the index. EfConstruction has to be at least 2 * m
    /// </summary>
    public int EfConstruction { get; set; }

    /// <summary>
    /// EfSearch: The size of the dynamic candidate list for search (40 by default). A higher value provides better recall at
    /// the cost of speed.
    /// </summary>
    public int EfSearch { get; set; }

    /// <summary>
    /// Initialize the AzureCosmosDBMongoDBConfig with default values
    /// </summary>
    public AzureCosmosDBMongoDBConfig()
    {
        this.ApplicationName = HttpHeaderConstant.Values.UserAgent;
        this.IndexName = "default_index";
        this.Kind = AzureCosmosDBVectorSearchType.VectorHNSW;
        this.NumLists = 1;
        this.Similarity = AzureCosmosDBSimilarityType.Cosine;
        this.NumberOfConnections = 16;
        this.EfConstruction = 64;
        this.EfSearch = 40;
    }
}

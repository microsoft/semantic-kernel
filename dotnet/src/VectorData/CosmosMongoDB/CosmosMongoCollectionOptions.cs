// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.CosmosMongoDB;

/// <summary>
/// Options when creating a <see cref="CosmosMongoCollection{TKey, TRecord}"/>.
/// </summary>
public sealed class CosmosMongoCollectionOptions : VectorStoreCollectionOptions
{
    internal static readonly CosmosMongoCollectionOptions Default = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="CosmosMongoCollectionOptions"/> class.
    /// </summary>
    public CosmosMongoCollectionOptions()
    {
    }

    internal CosmosMongoCollectionOptions(CosmosMongoCollectionOptions? source) : base(source)
    {
        this.NumLists = source?.NumLists ?? Default.NumLists;
        this.EfConstruction = source?.EfConstruction ?? Default.EfConstruction;
        this.EfSearch = source?.EfSearch ?? Default.EfSearch;
    }

    /// <summary>
    /// This integer is the number of clusters that the inverted file (IVF) index uses to group the vector data. Default is 1.
    /// We recommend that numLists is set to documentCount/1000 for up to 1 million documents and to sqrt(documentCount)
    /// for more than 1 million documents. Using a numLists value of 1 is akin to performing brute-force search, which has
    /// limited performance.
    /// </summary>
    public int NumLists { get; set; } = 1;

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

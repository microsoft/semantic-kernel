// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using MongoDB.Bson;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// Options when creating a <see cref="AzureCosmosDBMongoDBVectorStoreRecordCollection{TRecord}"/>.
/// </summary>
public sealed class AzureCosmosDBMongoDBVectorStoreRecordCollectionOptions<TRecord>
{
    /// <summary>
    /// Gets or sets an optional custom mapper to use when converting between the data model and the Azure CosmosDB MongoDB BSON object.
    /// </summary>
    public IVectorStoreRecordMapper<TRecord, BsonDocument>? BsonDocumentCustomMapper { get; init; } = null;

    /// <summary>
    /// Gets or sets an optional record definition that defines the schema of the record type.
    /// </summary>
    /// <remarks>
    /// If not provided, the schema will be inferred from the record model class using reflection.
    /// In this case, the record model properties must be annotated with the appropriate attributes to indicate their usage.
    /// See <see cref="VectorStoreRecordKeyAttribute"/>, <see cref="VectorStoreRecordDataAttribute"/> and <see cref="VectorStoreRecordVectorAttribute"/>.
    /// </remarks>
    public VectorStoreRecordDefinition? VectorStoreRecordDefinition { get; init; } = null;

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
<<<<<<< main
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    public int? EfConstruction { get; set; } = null;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    public int? EfConstruction { get; set; } = null;
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    public int? EfConstruction { get; set; } = null;
=======
>>>>>>> Stashed changes
=======
    public int? EfConstruction { get; set; } = null;
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
=======
>>>>>>> upstream/main
    public int EfConstruction { get; set; } = 64;

    /// <summary>
    /// The size of the dynamic candidate list for search (40 by default). A higher value provides better recall at
    /// the cost of speed.
    /// </summary>
    public int EfSearch { get; set; } = 40;
<<<<<<< main
=======
    public int? EfConstruction { get; set; } = null;
>>>>>>> 6d73513a859ab2d05e01db3bc1d405827799e34b
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
<<<<<<< main
=======
>>>>>>> upstream/main
=======
>>>>>>> head
>>>>>>> div
}

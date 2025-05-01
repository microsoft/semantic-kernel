// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Reflection;
using MongoDB.Bson;
using MongoDB.Bson.Serialization.Attributes;

// ReSharper disable InconsistentNaming
namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// Similarity metric to use with the index. Possible options are COS (cosine distance), L2 (Euclidean distance), and IP (inner product).
/// </summary>
[Obsolete("The IMemoryStore abstraction is being phased out, use Microsoft.Extensions.VectorData and AzureMongoDBMongoDBVectorStore")]
public enum AzureCosmosDBSimilarityType
{
    /// <summary>
    /// Cosine similarity
    /// </summary>
    [BsonElement("COS")]
    Cosine,

    /// <summary>
    /// Inner Product similarity
    /// </summary>
    [BsonElement("IP")]
    InnerProduct,

    /// <summary>
    /// Euclidean similarity
    /// </summary>
    [BsonElement("L2")]
    Euclidean
}

[Obsolete("The IMemoryStore abstraction is being phased out, use Microsoft.Extensions.VectorData and AzureMongoDBMongoDBVectorStore")]
internal static class AzureCosmosDBSimilarityTypeExtensions
{
    public static string GetCustomName(this AzureCosmosDBSimilarityType type)
    {
        var attribute = type.GetType().GetField(type.ToString())?.GetCustomAttribute<BsonElementAttribute>();
        return attribute?.ElementName ?? type.ToString();
    }
}

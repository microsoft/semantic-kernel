// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Reflection;
using MongoDB.Bson.Serialization.Attributes;

// ReSharper disable InconsistentNaming
namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBMongoDB;

/// <summary>
/// Type of vector index to create. The options are vector-ivf and vector-hnsw.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being phased out, use Microsoft.Extensions.VectorData and AzureMongoDBMongoDBVectorStore")]
public enum AzureCosmosDBVectorSearchType
{
    /// <summary>
    /// vector-ivf is available on all cluster tiers
    /// </summary>
    [BsonElement("vector-ivf")]
    VectorIVF,

    /// <summary>
    /// vector-hnsw is available on M40 cluster tiers and higher.
    /// </summary>
    [BsonElement("vector-hnsw")]
    VectorHNSW
}

[Obsolete("The IMemoryStore abstraction is being phased out, use Microsoft.Extensions.VectorData and AzureMongoDBMongoDBVectorStore")]
internal static class AzureCosmosDBVectorSearchTypeExtensions
{
    public static string GetCustomName(this AzureCosmosDBVectorSearchType type)
    {
        var attribute = type.GetType().GetField(type.ToString())?.GetCustomAttribute<BsonElementAttribute>();
        return attribute?.ElementName ?? type.ToString();
    }
}

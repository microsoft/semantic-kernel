// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

internal static class PostgresConstants
{
    /// <summary>The name of this vector store for telemetry purposes.</summary>
    public const string VectorStoreSystemName = "postgresql";

    /// <summary>Validation options.</summary>
    public static readonly VectorStoreRecordModelBuildingOptions ModelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,

        SupportedKeyPropertyTypes =
        [
            typeof(short),
            typeof(int),
            typeof(long),
            typeof(string),
            typeof(Guid)
        ],

        SupportedDataPropertyTypes =
        [
            typeof(bool),
            typeof(short),
            typeof(int),
            typeof(long),
            typeof(float),
            typeof(double),
            typeof(decimal),
            typeof(string),
            typeof(DateTime),
            typeof(DateTimeOffset),
            typeof(Guid),
            typeof(byte[]),
        ],

        SupportedEnumerableDataPropertyElementTypes =
        [
            typeof(bool),
            typeof(short),
            typeof(int),
            typeof(long),
            typeof(float),
            typeof(double),
            typeof(decimal),
            typeof(string),
            typeof(DateTime),
            typeof(DateTimeOffset),
            typeof(Guid),
        ],

        SupportedVectorPropertyTypes =
        [
            typeof(ReadOnlyMemory<float>),
            typeof(ReadOnlyMemory<float>?)
        ]
    };

    /// <summary>A <see cref="HashSet{T}"/> of types that vector properties on the provided model may have.</summary>
    public static readonly HashSet<Type> SupportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?)
    ];

    /// <summary>The default schema name.</summary>
    public const string DefaultSchema = "public";

    /// <summary>The name of the column that returns distance value in the database.</summary>
    /// <remarks>It is used in the similarity search query. Must not conflict with model property.</remarks>
    public const string DistanceColumnName = "sk_pg_distance";

    /// <summary>The default index kind.</summary>
    /// <remarks>Defaults to "Flat", which means no indexing.</remarks>
    public const string DefaultIndexKind = IndexKind.Flat;

    /// <summary>The default distance function.</summary>
    public const string DefaultDistanceFunction = DistanceFunction.CosineDistance;

    public static readonly Dictionary<string, int> IndexMaxDimensions = new()
    {
        { IndexKind.Hnsw, 2000 },
    };
}

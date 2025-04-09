// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

internal static class PostgresConstants
{
    /// <summary>The name of this database for telemetry purposes.</summary>
    public const string DatabaseName = "Postgres";

    /// <summary>A <see cref="HashSet{T}"/> of types that a key on the provided model may have.</summary>
    public static readonly HashSet<Type> SupportedKeyTypes =
    [
        typeof(short),
        typeof(int),
        typeof(long),
        typeof(string),
        typeof(Guid),
    ];

    /// <summary>A <see cref="HashSet{T}"/> of types that data properties on the provided model may have.</summary>
    public static readonly HashSet<Type> SupportedDataTypes =
    [
        typeof(bool),
        typeof(bool?),
        typeof(short),
        typeof(short?),
        typeof(int),
        typeof(int?),
        typeof(long),
        typeof(long?),
        typeof(float),
        typeof(float?),
        typeof(double),
        typeof(double?),
        typeof(decimal),
        typeof(decimal?),
        typeof(string),
        typeof(DateTime),
        typeof(DateTime?),
        typeof(DateTimeOffset),
        typeof(DateTimeOffset?),
        typeof(Guid),
        typeof(Guid?),
        typeof(byte[]),
    ];

    /// <summary>A <see cref="HashSet{T}"/> of types that enumerable data properties on the provided model may use as their element types.</summary>
    public static readonly HashSet<Type> SupportedEnumerableDataElementTypes =
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
    ];

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

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

internal static class PostgresConstants
{
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
        typeof(DateTimeOffset),
        typeof(DateTimeOffset?),
        typeof(Guid),
        typeof(Guid?),
        typeof(byte[]),
        typeof(List<bool>),
        typeof(List<short>),
        typeof(List<int>),
        typeof(List<long>),
        typeof(List<float>),
        typeof(List<double>),
        typeof(List<decimal>),
        typeof(List<string>),
        typeof(List<DateTimeOffset>),
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
}

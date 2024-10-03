// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

internal static class SqliteConstants
{
    /// <summary>A <see cref="HashSet{T}"/> of types that a key on the provided model may have.</summary>
    public static readonly HashSet<Type> SupportedKeyTypes =
    [
        typeof(ulong),
        typeof(string)
    ];

    /// <summary>A <see cref="HashSet{T}"/> of types that data properties on the provided model may have.</summary>
    public static readonly HashSet<Type> SupportedDataTypes =
    [
        typeof(int),
        typeof(int?),
        typeof(long),
        typeof(long?),
        typeof(ulong),
        typeof(ulong?),
        typeof(short),
        typeof(short?),
        typeof(ushort),
        typeof(ushort?),
        typeof(string),
        typeof(bool),
        typeof(bool?),
        typeof(float),
        typeof(float?),
        typeof(double),
        typeof(double?),
        typeof(decimal),
        typeof(decimal?),
        typeof(byte[]),
        typeof(DateTime),
        typeof(DateTime?)
    ];

    /// <summary>A <see cref="HashSet{T}"/> of types that vector properties on the provided model may have.</summary>
    public static readonly HashSet<Type> SupportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?)
    ];
}

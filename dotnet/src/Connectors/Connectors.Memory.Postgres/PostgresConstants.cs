// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

internal static class PostgresConstants
{
    /// <summary>A <see cref="HashSet{T}"/> of types that a key on the provided model may have.</summary>
    public static readonly HashSet<Type> SupportedKeyTypes =
    [
        typeof(string),
        typeof(int),
        typeof(long),
        typeof(ulong),
        typeof(short),
        typeof(ushort),
    ];

    /// <summary>A <see cref="HashSet{T}"/> of types that data properties on the provided model may have.</summary>
    public static readonly HashSet<Type> SupportedDataTypes =
    [
        typeof(bool),
        typeof(bool?),
        typeof(short),
        typeof(short?),
        typeof(ushort),
        typeof(ushort?),
        typeof(int),
        typeof(int?),
        typeof(uint),
        typeof(uint?),
        typeof(long),
        typeof(long?),
        typeof(ulong),
        typeof(ulong?),
        typeof(float),
        typeof(float?),
        typeof(double),
        typeof(double?),
        typeof(decimal),
        typeof(decimal?),
        typeof(string),
        typeof(DateTimeOffset),
        typeof(DateTimeOffset?),
        typeof(byte[]),
        typeof(List<bool>),
        typeof(List<short>),
        typeof(List<ushort>),
        typeof(List<int>),
        typeof(List<uint>),
        typeof(List<long>),
        typeof(List<ulong>),
        typeof(List<float>),
        typeof(List<double>),
        typeof(List<decimal>),
        typeof(List<string>),
        typeof(List<DateTimeOffset>),
        typeof(bool[]),
        typeof(short[]),
        typeof(ushort[]),
        typeof(int[]),
        typeof(uint[]),
        typeof(long[]),
        typeof(ulong[]),
        typeof(float[]),
        typeof(double[]),
        typeof(decimal[]),
        typeof(string[]),
        typeof(DateTimeOffset[]),
    ];

    /// <summary>A <see cref="HashSet{T}"/> of types that vector properties on the provided model may have.</summary>
    public static readonly HashSet<Type> SupportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?)
    ];
}

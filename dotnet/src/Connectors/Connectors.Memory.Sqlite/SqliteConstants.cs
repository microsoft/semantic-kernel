// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

internal static class SqliteConstants
{
    internal const string VectorStoreSystemName = "sqlite";

    /// <summary>
    /// SQLite extension name for vector search.
    /// More information here: <see href="https://github.com/asg017/sqlite-vec"/>.
    /// </summary>
    public const string VectorSearchExtensionName = "vec0";

    /// <summary>A <see cref="HashSet{T}"/> of types that vector properties on the provided model may have.</summary>
    public static readonly HashSet<Type> SupportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?)
    ];

    public static readonly VectorStoreRecordModelBuildingOptions ModelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,

        SupportedKeyPropertyTypes =
        [
            typeof(ulong),
            typeof(string)
        ],

        SupportedDataPropertyTypes =
        [
            typeof(int),
            typeof(long),
            typeof(ulong),
            typeof(short),
            typeof(ushort),
            typeof(string),
            typeof(bool),
            typeof(float),
            typeof(double),
            typeof(decimal),
            typeof(byte[])
        ],

        SupportedEnumerableDataPropertyElementTypes = [],
        SupportedVectorPropertyTypes = SupportedVectorTypes,

        EscapeIdentifier = SqliteVectorStoreCollectionCommandBuilder.EscapeIdentifier
    };
}

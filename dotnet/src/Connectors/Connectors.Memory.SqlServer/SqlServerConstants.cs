// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal static class SqlServerConstants
{
    internal const string VectorStoreSystemName = "microsoft.sql_server";

    // The actual number is actually higher (2_100), but we want to avoid any kind of "off by one" errors.
    internal const int MaxParameterCount = 2_000;

    internal const int MaxIndexNameLength = 128;

    internal static readonly HashSet<Type> SupportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>), // VECTOR
        typeof(ReadOnlyMemory<float>?)
    ];

    public static readonly VectorStoreRecordModelBuildingOptions ModelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,

        SupportedKeyPropertyTypes =
        [
            typeof(int), // INT
            typeof(long), // BIGINT
            typeof(string), // VARCHAR
            typeof(Guid), // UNIQUEIDENTIFIER
            typeof(DateTime), // DATETIME2
            typeof(byte[]) // VARBINARY
        ],

        SupportedDataPropertyTypes =
        [
            typeof(int), // INT
            typeof(short), // SMALLINT
            typeof(byte), // TINYINT
            typeof(long), // BIGINT.
            typeof(Guid), // UNIQUEIDENTIFIER.
            typeof(string), // NVARCHAR
            typeof(byte[]), // VARBINARY
            typeof(bool), // BIT
            typeof(DateTime), // DATETIME2
#if NET
            // We don't support mapping TimeSpan to TIME on purpose
            // See https://github.com/microsoft/semantic-kernel/pull/10623#discussion_r1980350721
            typeof(TimeOnly), // TIME
#endif
            typeof(decimal), // DECIMAL
            typeof(double), // FLOAT
            typeof(float), // REAL
        ],

        SupportedEnumerableDataPropertyElementTypes = [],

        SupportedVectorPropertyTypes = SupportedVectorTypes
    };
}

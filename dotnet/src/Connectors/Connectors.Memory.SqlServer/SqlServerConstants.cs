// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal static class SqlServerConstants
{
    internal const string Schema = "dbo";

    internal static readonly HashSet<Type> SupportedKeyTypes =
    [
        typeof(int), // INT 
        typeof(long), // BIGINT
        typeof(string), // VARCHAR 
        typeof(Guid), // UNIQUEIDENTIFIER
        typeof(DateTime), // DATETIME
        typeof(byte[]) // VARBINARY
    ];

    internal static readonly HashSet<Type> SupportedAutoGenerateKeyTypes =
    [
        typeof(int), // IDENTITY
        typeof(long), // IDENTITY
        typeof(Guid) // NEWID
    ];

    internal static readonly HashSet<Type> SupportedDataTypes =
    [
        typeof(int), // INT
        typeof(short), // SMALLINT
        typeof(byte), // TINYINT
        typeof(long), // BIGINT.
        typeof(Guid), // UNIQUEIDENTIFIER.
        typeof(string), // NVARCHAR
        typeof(byte[]), //VARBINARY
        typeof(bool), // BIT
        typeof(DateTime), // DATETIME
        typeof(TimeSpan), // TIME
        typeof(decimal), // DECIMAL
        typeof(double), // FLOAT
        typeof(float), // REAL
    ];

    internal static readonly HashSet<Type> SupportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>), // VECTOR
        typeof(ReadOnlyMemory<float>?)
    ];
}

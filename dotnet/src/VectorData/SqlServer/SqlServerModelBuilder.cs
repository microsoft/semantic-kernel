// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal class SqlServerModelBuilder() : CollectionModelBuilder(s_modelBuildingOptions)
{
    internal const string SupportedVectorTypes = "ReadOnlyMemory<float>, Embedding<float>, float[]";

    private static readonly CollectionModelBuildingOptions s_modelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,
    };

    protected override bool IsKeyPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = "int, long, string, Guid, DateTime, or byte[]";

        return type == typeof(int) // INT
            || type == typeof(long) // BIGINT
            || type == typeof(string) // VARCHAR
            || type == typeof(Guid) // UNIQUEIDENTIFIER
            || type == typeof(DateTime) // DATETIME2
            || type == typeof(byte[]); // VARBINARY
    }

    protected override bool IsDataPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = "string, int, long, double, float, bool, DateTimeOffset, or arrays/lists of these types";

        if (Nullable.GetUnderlyingType(type) is Type underlyingType)
        {
            type = underlyingType;
        }

        return type == typeof(int) // INT
            || type == typeof(short) // SMALLINT
            || type == typeof(byte) // TINYINT
            || type == typeof(long) // BIGINT.
            || type == typeof(Guid) // UNIQUEIDENTIFIER.
            || type == typeof(string) // NVARCHAR
            || type == typeof(byte[]) // VARBINARY
            || type == typeof(bool) // BIT
            || type == typeof(DateTime) // DATETIME2
#if NET
            // We don't support mapping TimeSpan to TIME on purpose
            // See https://github.com/microsoft/semantic-kernel/pull/10623#discussion_r1980350721
            || type == typeof(TimeOnly) // TIME
#endif
            || type == typeof(decimal) // DECIMAL
            || type == typeof(double) // FLOAT
            || type == typeof(float); // REAL
    }

    protected override bool IsVectorPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
        => IsVectorPropertyTypeValidCore(type, out supportedTypes);

    internal static bool IsVectorPropertyTypeValidCore(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = SupportedVectorTypes;

        return type == typeof(ReadOnlyMemory<float>)
            || type == typeof(ReadOnlyMemory<float>?)
            || type == typeof(Embedding<float>)
            || type == typeof(float[]);
    }
}

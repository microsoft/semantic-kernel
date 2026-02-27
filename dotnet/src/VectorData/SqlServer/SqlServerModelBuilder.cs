// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Data.SqlTypes;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal class SqlServerModelBuilder() : CollectionModelBuilder(s_modelBuildingOptions)
{
    internal const string SupportedVectorTypes = "SqlVector<float>, ReadOnlyMemory<float>, Embedding<float>, float[]";
    internal const string SupportedIndexKinds = $"{IndexKind.Flat}, {IndexKind.DiskAnn}";

    private static readonly CollectionModelBuildingOptions s_modelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleVectors = true,
    };

    protected override bool SupportsKeyAutoGeneration(Type keyPropertyType)
        => keyPropertyType == typeof(Guid) || keyPropertyType == typeof(int) || keyPropertyType == typeof(long);

    protected override void ValidateKeyProperty(KeyPropertyModel keyProperty)
    {
        var type = keyProperty.Type;

        if (type != typeof(int) && type != typeof(long) && type != typeof(string) && type != typeof(Guid))
        {
            throw new NotSupportedException(
                $"Property '{keyProperty.ModelName}' has unsupported type '{type.Name}'. Key properties must be one of the supported types: int, long, string, Guid.");
        }
    }

    protected override void ValidateProperty(PropertyModel propertyModel, VectorStoreCollectionDefinition? definition)
    {
        base.ValidateProperty(propertyModel, definition);

        if (propertyModel is VectorPropertyModel vectorProperty)
        {
            switch (vectorProperty.IndexKind)
            {
                case IndexKind.Flat or IndexKind.DiskAnn or null or "":
                    break;
                default:
                    throw new NotSupportedException(
                        $"Index kind '{vectorProperty.IndexKind}' is not supported by the SQL Server connector. Supported index kinds: {SupportedIndexKinds}");
            }
        }
    }

    protected override bool IsDataPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = "string, short, int, long, double, float, decimal, bool, DateTime, DateTimeOffset, DateOnly, TimeOnly, Guid, byte[], string[], List<string>";

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
            || type == typeof(DateTimeOffset) // DATETIMEOFFSET
#if NET
            || type == typeof(DateOnly) // DATE
                                        // We don't support mapping TimeSpan to TIME on purpose
                                        // See https://github.com/microsoft/semantic-kernel/pull/10623#discussion_r1980350721
            || type == typeof(TimeOnly) // TIME
#endif
            || type == typeof(decimal) // DECIMAL
            || type == typeof(double) // FLOAT
            || type == typeof(float) // REAL

            // We map string[] to the SQL Server 2025 JSON data type (anyone using vector search is already using 2025)
            || type == typeof(string[]) // JSON
            || type == typeof(List<string>); // JSON
    }

    protected override bool IsVectorPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
        => IsVectorPropertyTypeValidCore(type, out supportedTypes);

    internal static bool IsVectorPropertyTypeValidCore(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = SupportedVectorTypes;

        return type == typeof(ReadOnlyMemory<float>)
            || type == typeof(ReadOnlyMemory<float>?)
            || type == typeof(Embedding<float>)
            || type == typeof(float[])
            // SqlClient-specific type representing a vector
            || type == typeof(SqlVector<float>)
            || type == typeof(SqlVector<float>?);
    }
}

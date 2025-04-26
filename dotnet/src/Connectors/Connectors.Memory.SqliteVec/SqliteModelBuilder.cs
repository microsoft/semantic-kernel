// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.SqliteVec;

internal class SqliteModelBuilder() : CollectionModelBuilder(s_modelBuildingOptions)
{
    private static readonly CollectionModelBuildingOptions s_modelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,
        EscapeIdentifier = SqliteCommandBuilder.EscapeIdentifier
    };

    protected override bool IsKeyPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = "ulong, string";

        return type == typeof(ulong) || type == typeof(string);
    }

    protected override bool IsDataPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = "int, long, ulong, short, ushort, string, bool, float, double,decimal, byte[]";

        if (Nullable.GetUnderlyingType(type) is Type underlyingType)
        {
            type = underlyingType;
        }

        return type == typeof(int)
            || type == typeof(long)
            || type == typeof(ulong)
            || type == typeof(short)
            || type == typeof(ushort)
            || type == typeof(string)
            || type == typeof(bool)
            || type == typeof(float)
            || type == typeof(double)
            || type == typeof(decimal)
            || type == typeof(byte[]);
    }

    protected override bool IsVectorPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
        => IsVectorPropertyTypeValidCore(type, out supportedTypes);

    internal static bool IsVectorPropertyTypeValidCore(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = "ReadOnlyMemory<float>";

        return type == typeof(ReadOnlyMemory<float>) || type == typeof(ReadOnlyMemory<float>?);
    }
}

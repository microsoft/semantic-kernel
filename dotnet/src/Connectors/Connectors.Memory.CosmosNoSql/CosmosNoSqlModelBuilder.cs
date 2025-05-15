// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.CosmosNoSql;

internal class CosmosNoSqlModelBuilder() : CollectionJsonModelBuilder(s_modelBuildingOptions)
{
    internal const string SupportedVectorTypes = "ReadOnlyMemory<float>, Embedding<float>, float[], ReadOnlyMemory<byte>, Embedding<byte>, byte[], ReadOnlyMemory<sbyte>, Embedding<sbyte>, sbyte[]";

    private static readonly CollectionModelBuildingOptions s_modelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,
        UsesExternalSerializer = true,
        ReservedKeyStorageName = CosmosNoSqlConstants.ReservedKeyPropertyName
    };

    protected override bool IsKeyPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        // TODO: Cosmos supports other key types (int, Guid...)
        supportedTypes = "string";

        return type == typeof(string);
    }

    protected override bool IsDataPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = "string, int, long, double, float, bool, DateTimeOffset, or arrays/lists of these types";

        if (Nullable.GetUnderlyingType(type) is Type underlyingType)
        {
            type = underlyingType;
        }

        return IsValid(type)
            || (type.IsArray && IsValid(type.GetElementType()!))
            || (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(List<>) && IsValid(type.GenericTypeArguments[0]));

        static bool IsValid(Type type)
            => type == typeof(bool) ||
               type == typeof(string) ||
               type == typeof(int) ||
               type == typeof(long) ||
               type == typeof(float) ||
               type == typeof(double) ||
               type == typeof(DateTimeOffset);
    }

    protected override bool IsVectorPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
        => IsVectorPropertyTypeValidCore(type, out supportedTypes);

    internal static bool IsVectorPropertyTypeValidCore(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = SupportedVectorTypes;

        if (Nullable.GetUnderlyingType(type) is Type underlyingType)
        {
            type = underlyingType;
        }

        return type == typeof(ReadOnlyMemory<float>)
            || type == typeof(Embedding<float>)
            || type == typeof(float[])
            || type == typeof(ReadOnlyMemory<byte>)
            || type == typeof(Embedding<byte>)
            || type == typeof(byte[])
            || type == typeof(ReadOnlyMemory<sbyte>)
            || type == typeof(Embedding<sbyte>)
            || type == typeof(sbyte[]);
    }
}

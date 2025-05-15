// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal class WeaviateModelBuilder(bool hasNamedVectors) : CollectionJsonModelBuilder(GetModelBuildingOptions(hasNamedVectors))
{
    private static CollectionModelBuildingOptions GetModelBuildingOptions(bool hasNamedVectors)
    {
        return new()
        {
            RequiresAtLeastOneVector = !hasNamedVectors,
            SupportsMultipleKeys = false,
            SupportsMultipleVectors = hasNamedVectors,
            UsesExternalSerializer = true,
            ReservedKeyStorageName = WeaviateConstants.ReservedKeyPropertyName
        };
    }

    protected override bool IsKeyPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = "Guid";

        return type == typeof(Guid);
    }

    protected override bool IsDataPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = "string, bool, int, long, short, byte, float, double, decimal, DateTime, DateTimeOffset, Guid, or arrays/lists of these types";

        return IsValid(type)
            || (type.IsArray && IsValid(type.GetElementType()!))
            || (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(List<>) && IsValid(type.GenericTypeArguments[0]));

        static bool IsValid(Type type)
        {
            if (Nullable.GetUnderlyingType(type) is Type underlyingType)
            {
                type = underlyingType;
            }

            return type == typeof(string)
                || type == typeof(bool)
                || type == typeof(int)
                || type == typeof(long)
                || type == typeof(short)
                || type == typeof(byte)
                || type == typeof(float)
                || type == typeof(double)
                || type == typeof(decimal)
                || type == typeof(DateTime)
                || type == typeof(DateTimeOffset)
                || type == typeof(Guid);
        }
    }

    protected override bool IsVectorPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
        => IsVectorPropertyTypeValidCore(type, out supportedTypes);

    internal static bool IsVectorPropertyTypeValidCore(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = "ReadOnlyMemory<float>";

        return type == typeof(ReadOnlyMemory<float>) || type == typeof(ReadOnlyMemory<float>?);
    }
}

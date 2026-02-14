// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

internal class PostgresModelBuilder() : CollectionModelBuilder(PostgresModelBuilder.ModelBuildingOptions)
{
    internal const string SupportedVectorTypes = "ReadOnlyMemory<float>, Embedding<float>, float[], ReadOnlyMemory<Half>, Embedding<Half>, Half[], BinaryEmbedding, BitArray, or SparseVector";

    public static readonly CollectionModelBuildingOptions ModelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,
    };

    protected override bool SupportsKeyAutoGeneration(Type keyPropertyType)
        => keyPropertyType == typeof(Guid) || keyPropertyType == typeof(int) || keyPropertyType == typeof(long);

    protected override void ValidateKeyProperty(KeyPropertyModel keyProperty)
    {
        var type = keyProperty.Type;

        if (type != typeof(short)
            && type != typeof(int)
            && type != typeof(long)
            && type != typeof(string)
            && type != typeof(Guid))
        {
            throw new NotSupportedException(
                $"Property '{keyProperty.ModelName}' has unsupported type '{type.Name}'. Key properties must be one of the supported types: short, int, long, string, Guid.");
        }
    }

    protected override bool IsDataPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = "bool, short, int, long, float, double, decimal, string, DateTime, DateTimeOffset, Guid, or arrays/lists of these types";

        if (Nullable.GetUnderlyingType(type) is Type underlyingType)
        {
            type = underlyingType;
        }

        return IsValid(type)
            || (type.IsArray && IsValid(type.GetElementType()!))
            || (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(List<>) && IsValid(type.GenericTypeArguments[0]));

        static bool IsValid(Type type)
            => type == typeof(bool) ||
                type == typeof(short) ||
                type == typeof(int) ||
                type == typeof(long) ||
                type == typeof(float) ||
                type == typeof(double) ||
                type == typeof(decimal) ||
                type == typeof(string) ||
                type == typeof(byte[]) ||
                type == typeof(DateTime) ||
                type == typeof(DateTimeOffset) ||
                type == typeof(Guid);
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

        return type == typeof(ReadOnlyMemory<float>) ||
            type == typeof(Embedding<float>) ||
            type == typeof(float[]) ||
#if NET
            type == typeof(ReadOnlyMemory<Half>) ||
            type == typeof(Embedding<Half>) ||
            type == typeof(Half[]) ||
#endif
            type == typeof(BinaryEmbedding) ||
            type == typeof(BitArray) ||
            type == typeof(SparseVector);
    }

    /// <inheritdoc />
    protected override void ValidateProperty(PropertyModel propertyModel, VectorStoreCollectionDefinition? definition)
    {
        base.ValidateProperty(propertyModel, definition);

        if (propertyModel.IsTimestampWithoutTimezone())
        {
            var type = Nullable.GetUnderlyingType(propertyModel.Type) ?? propertyModel.Type;
            if (type != typeof(DateTime))
            {
                throw new NotSupportedException(
                    $"Property '{propertyModel.ModelName}' has store type 'timestamp' configured, but this is only supported for DateTime properties. The property type is '{propertyModel.Type.Name}'.");
            }
        }
    }

    /// <inheritdoc />
    protected override Type? ResolveEmbeddingType(
        VectorPropertyModel vectorProperty,
        IEmbeddingGenerator embeddingGenerator,
        Type? userRequestedEmbeddingType)
        => vectorProperty.ResolveEmbeddingType<Embedding<float>>(embeddingGenerator, userRequestedEmbeddingType)
#if NET
        ?? vectorProperty.ResolveEmbeddingType<Embedding<Half>>(embeddingGenerator, userRequestedEmbeddingType)
#endif
        ?? vectorProperty.ResolveEmbeddingType<BinaryEmbedding>(embeddingGenerator, userRequestedEmbeddingType);
}

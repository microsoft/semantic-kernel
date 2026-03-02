// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.Redis;

internal class RedisModelBuilder(CollectionModelBuildingOptions options) : CollectionModelBuilder(options)
{
    internal const string SupportedVectorTypes = "ReadOnlyMemory<float>, Embedding<float>, float[], ReadOnlyMemory<double>, Embedding<double>, double[]";

    /// <inheritdoc />
    protected override Type? ResolveEmbeddingType(
        VectorPropertyModel vectorProperty,
        IEmbeddingGenerator embeddingGenerator,
        Type? userRequestedEmbeddingType)
        => vectorProperty.ResolveEmbeddingType<Embedding<float>>(embeddingGenerator, userRequestedEmbeddingType)
            ?? vectorProperty.ResolveEmbeddingType<Embedding<double>>(embeddingGenerator, userRequestedEmbeddingType);

    protected override void ValidateKeyProperty(KeyPropertyModel keyProperty)
    {
        base.ValidateKeyProperty(keyProperty);

        var type = keyProperty.Type;

        if (type != typeof(string) && type != typeof(Guid))
        {
            throw new NotSupportedException(
                $"Property '{keyProperty.ModelName}' has unsupported type '{type.Name}'. Key properties must be one of the supported types: string, Guid.");
        }
    }

    protected override bool IsDataPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = "string, int, uint, long, ulong, double, float";

        if (Nullable.GetUnderlyingType(type) is Type underlyingType)
        {
            type = underlyingType;
        }

        return type == typeof(string)
            || type == typeof(int)
            || type == typeof(uint)
            || type == typeof(long)
            || type == typeof(ulong)
            || type == typeof(double)
            || type == typeof(float);
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
            || type == typeof(ReadOnlyMemory<double>)
            || type == typeof(Embedding<double>)
            || type == typeof(double[]);
    }

    /// <inheritdoc />
    protected override void ValidateProperty(PropertyModel propertyModel, VectorStoreCollectionDefinition? definition)
    {
        base.ValidateProperty(propertyModel, definition);

        ValidateStorageName(propertyModel);
    }

    internal static void ValidateStorageName(PropertyModel propertyModel)
    {
        // RediSearch field names cannot be escaped in all contexts; storage names are validated during model building.
        if (!IsValidIdentifier(propertyModel.StorageName))
        {
            throw new InvalidOperationException(
                $"Property '{propertyModel.ModelName}' has storage name '{propertyModel.StorageName}' which is not a valid RediSearch field name. " +
                "RediSearch field names must start with a letter or underscore, and contain only letters, digits, and underscores.");
        }
    }

    internal static bool IsValidIdentifier(string name)
    {
        if (string.IsNullOrEmpty(name))
        {
            return false;
        }

        var first = name[0];
        if (!char.IsLetter(first) && first != '_')
        {
            return false;
        }

        for (var i = 1; i < name.Length; i++)
        {
            var c = name[i];
            if (!char.IsLetterOrDigit(c) && c != '_')
            {
                return false;
            }
        }

        return true;
    }
}

﻿// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.Redis;

internal class RedisModelBuilder(CollectionModelBuildingOptions options) : CollectionModelBuilder(options)
{
    internal const string SupportedVectorTypes = "ReadOnlyMemory<float>, Embedding<float>, float[], ReadOnlyMemory<double>, Embedding<double>, double[]";

    /// <inheritdoc />
    protected override void SetupEmbeddingGeneration(
        VectorPropertyModel vectorProperty,
        IEmbeddingGenerator embeddingGenerator,
        Type? embeddingType)
    {
        if (!vectorProperty.TrySetupEmbeddingGeneration<Embedding<float>, ReadOnlyMemory<float>>(embeddingGenerator, embeddingType)
            && !vectorProperty.TrySetupEmbeddingGeneration<Embedding<double>, ReadOnlyMemory<double>>(embeddingGenerator, embeddingType)
            )
        {
            throw new InvalidOperationException(
                VectorDataStrings.IncompatibleEmbeddingGenerator(
                    embeddingGeneratorType: embeddingGenerator.GetType(),
                    supportedInputTypes: vectorProperty.GetSupportedInputTypes(),
                    supportedOutputTypes:
                    [
                        typeof(ReadOnlyMemory<float>),
                        typeof(ReadOnlyMemory<double>)
                    ]));
        }
    }

    protected override bool IsKeyPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = "string";

        return type == typeof(string);
    }

    protected override bool IsDataPropertyTypeValid(Type type, [NotNullWhen(false)] out string? supportedTypes)
    {
        supportedTypes = "string, int, uint, long, ulong, double, float, bool";

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
            || type == typeof(float)
            || type == typeof(bool);
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
}

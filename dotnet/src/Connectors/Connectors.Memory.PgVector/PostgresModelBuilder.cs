// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;
using Pgvector;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

internal class PostgresModelBuilder() : CollectionModelBuilder(PostgresModelBuilder.ModelBuildingOptions)
{
    public static readonly HashSet<Type> SupportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?),

#if NET8_0_OR_GREATER
        typeof(ReadOnlyMemory<Half>),
        typeof(ReadOnlyMemory<Half>?),
#endif

        typeof(BitArray),
        typeof(SparseVector)
    ];

    public static readonly CollectionModelBuildingOptions ModelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,

        SupportedKeyPropertyTypes =
        [
            typeof(short),
            typeof(int),
            typeof(long),
            typeof(string),
            typeof(Guid)
        ],

        SupportedDataPropertyTypes =
        [
            typeof(bool),
            typeof(short),
            typeof(int),
            typeof(long),
            typeof(float),
            typeof(double),
            typeof(decimal),
            typeof(string),
            typeof(DateTime),
            typeof(DateTimeOffset),
            typeof(Guid),
            typeof(byte[]),
        ],

        SupportedEnumerableDataPropertyElementTypes =
        [
            typeof(bool),
            typeof(short),
            typeof(int),
            typeof(long),
            typeof(float),
            typeof(double),
            typeof(decimal),
            typeof(string),
            typeof(DateTime),
            typeof(DateTimeOffset),
            typeof(Guid)
        ],

        SupportedVectorPropertyTypes = SupportedVectorTypes
    };

    /// <inheritdoc />
    protected override void SetupEmbeddingGeneration(
        VectorPropertyModel vectorProperty,
        IEmbeddingGenerator embeddingGenerator,
        Type? embeddingType)
    {
        if (!vectorProperty.TrySetupEmbeddingGeneration<Embedding<float>, ReadOnlyMemory<float>>(embeddingGenerator, embeddingType)
#if NET8_0_OR_GREATER
            && !vectorProperty.TrySetupEmbeddingGeneration<Embedding<Half>, ReadOnlyMemory<Half>>(embeddingGenerator, embeddingType)
#endif
            )
        {
            throw new InvalidOperationException(
                VectorDataStrings.IncompatibleEmbeddingGenerator(
                    embeddingGeneratorType: embeddingGenerator.GetType(),
                    supportedInputTypes: vectorProperty.GetSupportedInputTypes(),
                    supportedOutputTypes:
                    [
                        typeof(ReadOnlyMemory<float>),
#if NET8_0_OR_GREATER
                        typeof(ReadOnlyMemory<Half>)
#endif
                    ]));
        }
    }
}

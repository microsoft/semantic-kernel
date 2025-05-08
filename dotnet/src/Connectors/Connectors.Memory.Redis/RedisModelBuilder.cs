// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

internal class RedisModelBuilder(CollectionModelBuildingOptions options) : CollectionModelBuilder(options)
{
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
}

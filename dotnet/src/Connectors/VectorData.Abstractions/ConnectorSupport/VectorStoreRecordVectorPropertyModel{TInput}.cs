// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.Extensions.VectorData.ConnectorSupport;

/// <inheritdoc />
[Experimental("MEVD9001")]
public sealed class VectorStoreRecordVectorPropertyModel<TInput>(string modelName) : VectorStoreRecordVectorPropertyModel(modelName, typeof(TInput))
{
    /// <inheritdoc />
    public override bool TrySetupEmbeddingGeneration<TEmbedding, TUnwrappedEmbedding>(IEmbeddingGenerator embeddingGenerator, Type? embeddingType)
    {
        switch (embeddingGenerator)
        {
            case IEmbeddingGenerator<TInput, TEmbedding> when this.Type == typeof(TInput) && (embeddingType is null || embeddingType == typeof(TUnwrappedEmbedding)):
                this.EmbeddingGenerator = embeddingGenerator;
                this.EmbeddingType = embeddingType ?? typeof(TUnwrappedEmbedding);

                return true;

            case null:
                throw new UnreachableException("This method should only be called when an embedding generator is configured.");
            default:
                return false;
        }
    }

    /// <inheritdoc />
    public override bool TryGenerateEmbedding<TRecord, TEmbedding, TUnwrappedEmbedding>(TRecord record, CancellationToken cancellationToken, [NotNullWhen(true)] out Task<TEmbedding>? task)
    {
        switch (this.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<TInput, TEmbedding> generator when this.EmbeddingType == typeof(TUnwrappedEmbedding):
                task = generator.GenerateAsync(
                    this.GetValueAsObject(record) is var value && value is TInput s
                        ? s
                        : throw new InvalidOperationException($"Property '{this.ModelName}' was configured with an embedding generator accepting a {nameof(TInput)}, but {value?.GetType().Name ?? "null"} was provided."),
                    options: null,
                    cancellationToken);
                return true;

            case null:
                throw new UnreachableException("This method should only be called when an embedding generator is configured.");

            default:
                task = null;
                return false;
        }
    }

    /// <inheritdoc />
    public override bool TryGenerateEmbeddings<TRecord, TEmbedding, TUnwrappedEmbedding>(IEnumerable<TRecord> records, CancellationToken cancellationToken, [NotNullWhen(true)] out Task<GeneratedEmbeddings<TEmbedding>>? task)
    {
        switch (this.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<TInput, TEmbedding> generator when this.EmbeddingType == typeof(TUnwrappedEmbedding):
                task = generator.GenerateAsync(
                    records.Select(r => this.GetValueAsObject(r) is var value && value is TInput s
                        ? s
                        : throw new InvalidOperationException($"Property '{this.ModelName}' was configured with an embedding generator accepting a string, but {value?.GetType().Name ?? "null"} was provided.")),
                    options: null,
                    cancellationToken);
                return true;

            case null:
                throw new UnreachableException("This method should only be called when an embedding generator is configured.");

            default:
                task = null;
                return false;
        }
    }

    /// <inheritdoc />
    public override Type[] GetSupportedInputTypes() => [typeof(TInput)];
}

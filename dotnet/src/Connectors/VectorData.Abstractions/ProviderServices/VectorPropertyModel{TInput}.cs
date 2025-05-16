// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;

namespace Microsoft.Extensions.VectorData.ProviderServices;

/// <inheritdoc />
[Experimental("MEVD9001")]
public sealed class VectorPropertyModel<TInput>(string modelName) : VectorPropertyModel(modelName, typeof(TInput))
{
    /// <inheritdoc />
    public override Type? ResolveEmbeddingType<TEmbedding>(IEmbeddingGenerator embeddingGenerator, Type? userRequestedEmbeddingType)
        => embeddingGenerator switch
        {
            IEmbeddingGenerator<TInput, TEmbedding> when this.Type == typeof(TInput) && (userRequestedEmbeddingType is null || userRequestedEmbeddingType == typeof(TEmbedding))
                => typeof(TEmbedding),

            null => throw new ArgumentNullException(nameof(embeddingGenerator), "This method should only be called when an embedding generator is configured."),
            _ => null
        };

    /// <inheritdoc />
    public override bool TryGenerateEmbedding<TRecord, TEmbedding>(TRecord record, CancellationToken cancellationToken, [NotNullWhen(true)] out Task<TEmbedding>? task)
    {
        switch (this.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<TInput, TEmbedding> generator when this.EmbeddingType == typeof(TEmbedding):
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
    public override bool TryGenerateEmbeddings<TRecord, TEmbedding>(IEnumerable<TRecord> records, CancellationToken cancellationToken, [NotNullWhen(true)] out Task<GeneratedEmbeddings<TEmbedding>>? task)
    {
        switch (this.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<TInput, TEmbedding> generator when this.EmbeddingType == typeof(TEmbedding):
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

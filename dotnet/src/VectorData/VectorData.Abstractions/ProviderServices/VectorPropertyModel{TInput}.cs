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
    public override bool CanGenerateEmbedding<TEmbedding>(IEmbeddingGenerator embeddingGenerator)
        => embeddingGenerator is IEmbeddingGenerator<TInput, TEmbedding>
        || base.CanGenerateEmbedding<TEmbedding>(embeddingGenerator);

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
    internal override async Task<IReadOnlyList<Embedding>> GenerateEmbeddingsCoreAsync<TEmbedding>(IEnumerable<object?> values, CancellationToken cancellationToken)
    {
        switch (this.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<TInput, TEmbedding> generator when this.EmbeddingType == typeof(TEmbedding):
                return await generator.GenerateAsync(
                    values.Select(v => v is TInput s
                        ? s
                        : throw new InvalidOperationException($"Property '{this.ModelName}' was configured with an embedding generator accepting a {typeof(TInput).Name}, but {v?.GetType().Name ?? "null"} was provided.")),
                    options: null,
                    cancellationToken).ConfigureAwait(false);

            case null:
                throw new UnreachableException("This method should only be called when an embedding generator is configured.");

            default:
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{this.ModelName}' cannot produce an embedding of type '{typeof(TEmbedding).Name}' for the given input type.");
        }
    }

    /// <inheritdoc />
    internal override async Task<Embedding> GenerateEmbeddingCoreAsync<TEmbedding>(object? value, CancellationToken cancellationToken)
    {
        if (this.EmbeddingGenerator is IEmbeddingGenerator<TInput, TEmbedding> generator && value is TInput t)
        {
            return await generator.GenerateAsync(t, options: null, cancellationToken).ConfigureAwait(false);
        }

        // Fall through to base class which checks for string and DataContent input types.
        return await base.GenerateEmbeddingCoreAsync<TEmbedding>(value, cancellationToken).ConfigureAwait(false);
    }

    /// <inheritdoc />
    public override Type[] GetSupportedInputTypes() => [typeof(TInput)];
}

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

/// <summary>
/// Represents a vector property on a vector store record.
/// This is an internal support type meant for use by connectors only and not by applications.
/// </summary>
[Experimental("MEVD9001")]
public class VectorPropertyModel(string modelName, Type type) : PropertyModel(modelName, type)
{
    private int _dimensions;

    /// <summary>
    /// Gets or sets the number of dimensions that the vector has.
    /// </summary>
    /// <remarks>
    /// This property is required when creating collections, but can be omitted if not using that functionality.
    /// If not provided when trying to create a collection, create will fail.
    /// </remarks>
    public int Dimensions
    {
        get => this._dimensions;

        set
        {
            if (value <= 0)
            {
                throw new ArgumentOutOfRangeException(nameof(value), "Dimensions must be greater than zero.");
            }

            this._dimensions = value;
        }
    }

    /// <summary>
    /// Gets or sets the kind of index to use.
    /// </summary>
    /// <value>
    /// The default varies by database type. For more information, see the documentation of your chosen database connector.
    /// </value>
    /// <seealso cref="Microsoft.Extensions.VectorData.IndexKind"/>
    public string? IndexKind { get; set; }

    /// <summary>
    /// Gets or sets the distance function to use when comparing vectors.
    /// </summary>
    /// <value>
    /// The default varies by database type. For more information, see the documentation of your chosen database connector.
    /// </value>
    /// <seealso cref="Microsoft.Extensions.VectorData.DistanceFunction"/>
    public string? DistanceFunction { get; set; }

    /// <summary>
    /// Gets or sets the type representing the embedding stored in the database if <see cref="EmbeddingGenerator"/> is set.
    /// Otherwise, this property is identical to <see cref="Type"/>.
    /// </summary>
    // TODO: sort out the nullability story here: EmbeddingType must be non-null after model building is complete, but can be null during
    // model building as we're figuring things out (i.e. introduce a provider-facing interface where the property is non-nullable).
    [AllowNull]
    public Type EmbeddingType { get; set; } = null!;

    /// <summary>
    /// Gets or sets the embedding generator to use for this property.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }

    /// <summary>
    /// Gets or sets the <see cref="EmbeddingGenerationDispatcher"/> that was resolved for this property during model building.
    /// This handler is used for runtime embedding generation dispatch.
    /// </summary>
    /// <remarks>
    /// This is <see langword="null"/> for vector properties whose type is natively supported by the provider
    /// (e.g., <see cref="ReadOnlyMemory{T}"/> of <see langword="float"/>, <see langword="float"/>[], <see cref="Embedding{T}"/>),
    /// since no embedding generation is needed.
    /// </remarks>
    public EmbeddingGenerationDispatcher? EmbeddingGenerationDispatcher { get; set; }

    /// <summary>
    /// Checks whether the given <paramref name="embeddingGenerator" /> can produce embeddings of type <typeparamref name="TEmbedding" />
    /// for any input type known to this property model. The base implementation checks for <see cref="string"/> and <see cref="DataContent"/>;
    /// <see cref="VectorPropertyModel{TInput}"/> also checks for <c>TInput</c>.
    /// </summary>
    /// <remarks>This is used for native vector property types, where the input type isn't known at model-build time.</remarks>
    public virtual bool CanGenerateEmbedding<TEmbedding>(IEmbeddingGenerator embeddingGenerator)
        where TEmbedding : Embedding
        => embeddingGenerator is IEmbeddingGenerator<string, TEmbedding>
        || embeddingGenerator is IEmbeddingGenerator<DataContent, TEmbedding>;

    /// <summary>
    /// Checks whether the <see cref="EmbeddingGenerator"/> configured on this property supports the given embedding type.
    /// The implementation on this non-generic <see cref="VectorPropertyModel"/> checks for <see cref="string"/>
    /// and <see cref="DataContent"/> as input types for <see cref="EmbeddingGenerator"/>.
    /// </summary>
    public virtual Type? ResolveEmbeddingType<TEmbedding>(IEmbeddingGenerator embeddingGenerator, Type? userRequestedEmbeddingType)
        where TEmbedding : Embedding
        => embeddingGenerator switch
        {
            // On the TInput side, this out-of-the-box/simple implementation supports string and DataContent only
            // (users who want arbitrary TInput types need to use the generic subclass of this type).
            // The TEmbedding side is provided by the connector via the generic type parameter to this method, as the connector controls/knows which embedding types are supported.
            // Note that if the user has manually specified an embedding type (e.g. to choose Embedding<Half> rather than the default Embedding<float>),
            // that's provided via the userRequestedEmbeddingType argument; we use that as a filter.
            IEmbeddingGenerator<string, TEmbedding> when this.Type == typeof(string) && (userRequestedEmbeddingType is null || userRequestedEmbeddingType == typeof(TEmbedding))
                => typeof(TEmbedding),
            IEmbeddingGenerator<DataContent, TEmbedding> when this.Type == typeof(DataContent) && (userRequestedEmbeddingType is null || userRequestedEmbeddingType == typeof(TEmbedding))
                => typeof(TEmbedding),

            null => throw new ArgumentNullException(nameof(embeddingGenerator), "This method should only be called when an embedding generator is configured."),
            _ => null
        };

    /// <summary>
    /// Generates embeddings for the given <paramref name="values"/>, using the configured <see cref="EmbeddingGenerationDispatcher"/>.
    /// </summary>
    /// <exception cref="InvalidOperationException">Thrown if no <see cref="EmbeddingGenerationDispatcher"/> is configured on this property.</exception>
    public Task<IReadOnlyList<Embedding>> GenerateEmbeddingsAsync(IEnumerable<object?> values, CancellationToken cancellationToken)
        => this.EmbeddingGenerationDispatcher is not { } dispatcher
            ? throw new InvalidOperationException($"No embedding generation is configured for property '{this.ModelName}'.")
            : dispatcher.GenerateEmbeddingsAsync(this, values, cancellationToken);

    /// <summary>
    /// Generates a single embedding for the given <paramref name="value"/>, using the configured <see cref="EmbeddingGenerationDispatcher"/>.
    /// </summary>
    /// <exception cref="InvalidOperationException">Thrown if no <see cref="EmbeddingGenerationDispatcher"/> is configured on this property.</exception>
    public Task<Embedding> GenerateEmbeddingAsync(object? value, CancellationToken cancellationToken)
        => this.EmbeddingGenerationDispatcher is not { } dispatcher
            ? throw new InvalidOperationException($"No embedding generation is configured for property '{this.ModelName}'.")
            : dispatcher.GenerateEmbeddingAsync(this, value, cancellationToken);

    /// <summary>
    /// Core method to generate a batch of embeddings. Called by <see cref="EmbeddingGenerationDispatcher{TEmbedding}"/> with the correct type parameter.
    /// </summary>
    internal virtual async Task<IReadOnlyList<Embedding>> GenerateEmbeddingsCoreAsync<TEmbedding>(IEnumerable<object?> values, CancellationToken cancellationToken)
        where TEmbedding : Embedding
        => this.EmbeddingGenerator switch
        {
            IEmbeddingGenerator<string, TEmbedding> generator when this.EmbeddingType == typeof(TEmbedding)
                => await generator.GenerateAsync(
                    values.Select(v => v is string s
                        ? s
                        : throw new InvalidOperationException($"Property '{this.ModelName}' was configured with an embedding generator accepting a string, but {v?.GetType().Name ?? "null"} was provided.")),
                    options: null,
                    cancellationToken).ConfigureAwait(false),

            IEmbeddingGenerator<DataContent, TEmbedding> generator when this.EmbeddingType == typeof(TEmbedding)
                => await generator.GenerateAsync(
                    values.Select(v => v is DataContent c
                        ? c
                        : throw new InvalidOperationException($"Property '{this.ModelName}' was configured with an embedding generator accepting a {nameof(DataContent)}, but {v?.GetType().Name ?? "null"} was provided.")),
                    options: null,
                    cancellationToken).ConfigureAwait(false),

            null => throw new UnreachableException("This method should only be called when an embedding generator is configured."),

            _ => throw new InvalidOperationException(
                $"The embedding generator configured on property '{this.ModelName}' cannot produce an embedding of type '{typeof(TEmbedding).Name}' for the given input type."),
        };

    /// <summary>
    /// Core method to generate a single embedding. Called by <see cref="EmbeddingGenerationDispatcher{TEmbedding}"/> with the correct type parameter.
    /// </summary>
    internal virtual async Task<Embedding> GenerateEmbeddingCoreAsync<TEmbedding>(object? value, CancellationToken cancellationToken)
        where TEmbedding : Embedding
        => this.EmbeddingGenerator switch
        {
            IEmbeddingGenerator<string, TEmbedding> generator when value is string s
                => await generator.GenerateAsync(s, options: null, cancellationToken).ConfigureAwait(false),

            IEmbeddingGenerator<DataContent, TEmbedding> generator when value is DataContent c
                => await generator.GenerateAsync(c, options: null, cancellationToken).ConfigureAwait(false),

            null => throw new UnreachableException("This method should only be called when an embedding generator is configured."),

            _ => throw new InvalidOperationException(
                VectorDataStrings.IncompatibleEmbeddingGeneratorWasConfiguredForInputType(value?.GetType() ?? typeof(object), this.EmbeddingGenerator!.GetType())),
        };

    /// <summary>
    /// Returns the types of input that this property model supports.
    /// </summary>
    public virtual Type[] GetSupportedInputTypes() => [typeof(string), typeof(DataContent)];

    /// <inheritdoc/>
    public override string ToString()
        => $"{this.ModelName} (Vector, {this.Type.Name})";
}

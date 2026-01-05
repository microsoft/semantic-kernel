// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
#if !UNITY
#endif

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
#if !UNITY
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }

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
    /// Attempts to generate an embedding of type <typeparamref name="TEmbedding"/> from the vector property represented by this instance on the given <paramref name="record"/>, using
    /// the configured <see cref="EmbeddingGenerator"/>.
    /// </summary>
    /// <remarks>
    /// <para>
    /// If <see cref="EmbeddingGenerator"/> supports the given <typeparamref name="TEmbedding"/>, returns <see langword="true"/> and sets <paramref name="task"/> to a <see cref="Task"/>
    /// representing the embedding generation operation. If <see cref="EmbeddingGenerator"/> does not support the given <typeparamref name="TEmbedding"/>, returns <see langword="false"/>.
    /// </para>
    /// <para>
    /// The implementation on this non-generic <see cref="VectorPropertyModel"/> checks for <see cref="string"/>
    /// and <see cref="DataContent"/> as input types for <see cref="EmbeddingGenerator"/>.
    /// </para>
    /// </remarks>
    public virtual bool TryGenerateEmbedding<TRecord, TEmbedding>(TRecord record, CancellationToken cancellationToken, [NotNullWhen(true)] out Task<TEmbedding>? task)
        where TRecord : class
        where TEmbedding : Embedding
    {
        switch (this.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<string, TEmbedding> generator when this.EmbeddingType == typeof(TEmbedding):
            {
                task = generator.GenerateAsync(
                    this.GetValueAsObject(record) is var value && value is string s
                        ? s
                        : throw new InvalidOperationException($"Property '{this.ModelName}' was configured with an embedding generator accepting a string, but {value?.GetType().Name ?? "null"} was provided."),
                    options: null,
                    cancellationToken);
                return true;
            }

            case IEmbeddingGenerator<DataContent, TEmbedding> generator when this.EmbeddingType == typeof(TEmbedding):
            {
                task = generator.GenerateAsync(
                    this.GetValueAsObject(record) is var value && value is DataContent c
                        ? c
                        : throw new InvalidOperationException($"Property '{this.ModelName}' was configured with an embedding generator accepting a {nameof(DataContent)}, but {value?.GetType().Name ?? "null"} was provided."),
                    options: null,
                    cancellationToken);
                return true;
            }

            case null:
                throw new UnreachableException("This method should only be called when an embedding generator is configured.");

            default:
                task = null;
                return false;
        }
    }

    /// <summary>
    /// Attempts to generate embeddings of type <typeparamref name="TEmbedding"/> from the vector property represented by this instance on the given <paramref name="records"/>, using
    /// the configured <see cref="EmbeddingGenerator"/>.
    /// </summary>
    /// <remarks>
    /// <para>
    /// If <see cref="EmbeddingGenerator"/> supports the given <typeparamref name="TEmbedding"/>, returns <see langword="true"/> and sets <paramref name="task"/> to a <see cref="Task"/>
    /// representing the embedding generation operation. If <see cref="EmbeddingGenerator"/> does not support the given <typeparamref name="TEmbedding"/>, returns <see langword="false"/>.
    /// </para>
    /// <para>
    /// The implementation on this non-generic <see cref="VectorPropertyModel"/> checks for <see cref="string"/>
    /// and <see cref="DataContent"/> as input types for <see cref="EmbeddingGenerator"/>.
    /// </para>
    /// </remarks>
    public virtual bool TryGenerateEmbeddings<TRecord, TEmbedding>(IEnumerable<TRecord> records, CancellationToken cancellationToken, [NotNullWhen(true)] out Task<GeneratedEmbeddings<TEmbedding>>? task)
        where TRecord : class
        where TEmbedding : Embedding
    {
        switch (this.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<string, TEmbedding> generator when this.EmbeddingType == typeof(TEmbedding):
                task = generator.GenerateAsync(
                    records.Select(r => this.GetValueAsObject(r) is var value && value is string s
                        ? s
                        : throw new InvalidOperationException($"Property '{this.ModelName}' was configured with an embedding generator accepting a string, but {value?.GetType().Name ?? "null"} was provided.")),
                    options: null,
                    cancellationToken);
                return true;

            case IEmbeddingGenerator<DataContent, TEmbedding> generator when this.EmbeddingType == typeof(TEmbedding):
                task = generator.GenerateAsync(
                    records.Select(r => this.GetValueAsObject(r) is var value && value is DataContent c
                        ? c
                        : throw new InvalidOperationException($"Property '{this.ModelName}' was configured with an embedding generator accepting a {nameof(DataContent)}, but {value?.GetType().Name ?? "null"} was provided.")),
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

    /// <summary>
    /// Returns the types of input that this property model supports.
    /// </summary>
    public virtual Type[] GetSupportedInputTypes() => [typeof(string), typeof(DataContent)];
#else
    public object? EmbeddingGenerator { get; set; }

    /// <summary>
    /// Returns the types of input that this property model supports.
    /// </summary>
    public virtual Type[] GetSupportedInputTypes() => [typeof(string)];
#endif

    /// <inheritdoc/>
    public override string ToString()
        => $"{this.ModelName} (Vector, {this.Type.Name})";
}

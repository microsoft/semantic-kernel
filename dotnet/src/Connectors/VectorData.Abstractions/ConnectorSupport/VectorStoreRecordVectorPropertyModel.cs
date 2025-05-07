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

/// <summary>
/// Represents a vector property on a vector store record.
/// This is an internal support type meant for use by connectors only, and not for use by applications.
/// </summary>
[Experimental("MEVD9001")]
public class VectorStoreRecordVectorPropertyModel(string modelName, Type type) : VectorStoreRecordPropertyModel(modelName, type)
{
    private int _dimensions;

    /// <summary>
    /// The number of dimensions that the vector has.
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
    /// The kind of index to use.
    /// </summary>
    /// <value>
    /// The default varies by database type. See the documentation of your chosen database connector for more information.
    /// </value>
    /// <seealso cref="Microsoft.Extensions.VectorData.IndexKind"/>
    public string? IndexKind { get; set; }

    /// <summary>
    /// The distance function to use when comparing vectors.
    /// </summary>
    /// <value>
    /// The default varies by database type. See the documentation of your chosen database connector for more information.
    /// </value>
    /// <seealso cref="Microsoft.Extensions.VectorData.DistanceFunction"/>
    public string? DistanceFunction { get; set; }

    /// <summary>
    /// If <see cref="EmbeddingGenerator"/> is set, contains the type representing the embedding stored in the database.
    /// Otherwise, this property is identical to <see cref="Type"/>.
    /// </summary>
    public Type EmbeddingType { get; set; } = null!;

    /// <summary>
    /// The embedding generator to use for this property.
    /// </summary>
    public IEmbeddingGenerator? EmbeddingGenerator { get; set; }

    /// <summary>
    /// Checks whether the <see cref="EmbeddingGenerator"/> configured on this property supports the given embedding type.
    /// The implementation on this non-generic <see cref="VectorStoreRecordVectorPropertyModel"/> checks for <see cref="string"/>
    /// and <see cref="DataContent"/> as input types for <see cref="EmbeddingGenerator"/>.
    /// </summary>
    public virtual bool TrySetupEmbeddingGeneration<TEmbedding, TUnwrappedEmbedding>(IEmbeddingGenerator embeddingGenerator, Type? embeddingType)
        where TEmbedding : Embedding
    {
        // On the TInput side, this out-of-the-box/simple implementation supports string and DataContent only
        // (users who want arbitrary TInput types need to use the generic subclass of this type).
        // The TEmbedding side is provided by the connector via the generic type parameter to this method, as the connector controls/knows which embedding types are supported.
        // Note that if the user has manually specified an embedding type (e.g. to choose Embedding<Half> rather than the default Embedding<float>), that's provided via the embeddingType argument;
        // we use that as a filter below.
        switch (embeddingGenerator)
        {
            case IEmbeddingGenerator<string, TEmbedding> when this.Type == typeof(string) && (embeddingType is null || embeddingType == typeof(TUnwrappedEmbedding)):
            case IEmbeddingGenerator<DataContent, TEmbedding> when this.Type == typeof(DataContent) && (embeddingType is null || embeddingType == typeof(TUnwrappedEmbedding)):
                this.EmbeddingGenerator = embeddingGenerator;
                this.EmbeddingType = embeddingType ?? typeof(TUnwrappedEmbedding);

                return true;

            case null:
                throw new UnreachableException("This method should only be called when an embedding generator is configured.");
            default:
                return false;
        }
    }

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
    /// The implementation on this non-generic <see cref="VectorStoreRecordVectorPropertyModel"/> checks for <see cref="string"/>
    /// and <see cref="DataContent"/> as input types for <see cref="EmbeddingGenerator"/>.
    /// </para>
    /// </remarks>
    public virtual bool TryGenerateEmbedding<TRecord, TEmbedding, TUnwrappedEmbedding>(TRecord record, CancellationToken cancellationToken, [NotNullWhen(true)] out Task<TEmbedding>? task)
        where TRecord : notnull
        where TEmbedding : Embedding
    {
        switch (this.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<string, TEmbedding> generator when this.EmbeddingType == typeof(TUnwrappedEmbedding):
            {
                task = generator.GenerateAsync(
                    this.GetValueAsObject(record) is var value && value is string s
                        ? s
                        : throw new InvalidOperationException($"Property '{this.ModelName}' was configured with an embedding generator accepting a string, but {value?.GetType().Name ?? "null"} was provided."),
                    options: null,
                    cancellationToken);
                return true;
            }

            case IEmbeddingGenerator<DataContent, TEmbedding> generator when this.EmbeddingType == typeof(TUnwrappedEmbedding):
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
    /// The implementation on this non-generic <see cref="VectorStoreRecordVectorPropertyModel"/> checks for <see cref="string"/>
    /// and <see cref="DataContent"/> as input types for <see cref="EmbeddingGenerator"/>.
    /// </para>
    /// </remarks>
    public virtual bool TryGenerateEmbeddings<TRecord, TEmbedding, TUnwrappedEmbedding>(IEnumerable<TRecord> records, CancellationToken cancellationToken, [NotNullWhen(true)] out Task<GeneratedEmbeddings<TEmbedding>>? task)
        where TRecord : notnull
        where TEmbedding : Embedding
    {
        switch (this.EmbeddingGenerator)
        {
            case IEmbeddingGenerator<string, TEmbedding> generator when this.EmbeddingType == typeof(TUnwrappedEmbedding):
                task = generator.GenerateAsync(
                    records.Select(r => this.GetValueAsObject(r) is var value && value is string s
                        ? s
                        : throw new InvalidOperationException($"Property '{this.ModelName}' was configured with an embedding generator accepting a string, but {value?.GetType().Name ?? "null"} was provided.")),
                    options: null,
                    cancellationToken);
                return true;

            case IEmbeddingGenerator<DataContent, TEmbedding> generator when this.EmbeddingType == typeof(TUnwrappedEmbedding):
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

    /// <inheritdoc/>
    public override string ToString()
        => $"{this.ModelName} (Vector, {this.Type.Name})";
}

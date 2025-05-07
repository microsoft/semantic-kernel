// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Contains helper methods for mapping fields to and from the format required by the Redis client sdk.
/// </summary>
internal static class RedisVectorStoreRecordFieldMapping
{
    /// <summary>
    /// Convert a vector to a byte array as required by the Redis client sdk when using hashsets.
    /// </summary>
    /// <param name="vector">The vector to convert.</param>
    /// <returns>The byte array.</returns>
    public static byte[] ConvertVectorToBytes(ReadOnlyMemory<float> vector)
    {
        return MemoryMarshal.AsBytes(vector.Span).ToArray();
    }

    /// <summary>
    /// Convert a vector to a byte array as required by the Redis client sdk when using hashsets.
    /// </summary>
    /// <param name="vector">The vector to convert.</param>
    /// <returns>The byte array.</returns>
    public static byte[] ConvertVectorToBytes(ReadOnlyMemory<double> vector)
    {
        return MemoryMarshal.AsBytes(vector.Span).ToArray();
    }

    internal static async ValueTask<(IEnumerable<TRecord> records, IReadOnlyList<Embedding>?[]?)> ProcessEmbeddingsAsync<TRecord>(
        VectorStoreRecordModel model,
        IEnumerable<TRecord> records,
        CancellationToken cancellationToken)
        where TRecord : notnull
    {
        IReadOnlyList<TRecord>? recordsList = null;

        // If an embedding generator is defined, invoke it once per property for all records.
        IReadOnlyList<Embedding>?[]? generatedEmbeddings = null;

        var vectorPropertyCount = model.VectorProperties.Count;
        for (var i = 0; i < vectorPropertyCount; i++)
        {
            var vectorProperty = model.VectorProperties[i];

            if (vectorProperty.EmbeddingGenerator is null)
            {
                continue;
            }

            // We have a property with embedding generation; materialize the records' enumerable if needed, to
            // prevent multiple enumeration.
            if (recordsList is null)
            {
                recordsList = records is IReadOnlyList<TRecord> r ? r : records.ToList();

                if (recordsList.Count == 0)
                {
                    return (records, null);
                }

                records = recordsList;
            }

            // TODO: Ideally we'd group together vector properties using the same generator (and with the same input and output properties),
            // and generate embeddings for them in a single batch. That's some more complexity though.
            if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<float>, ReadOnlyMemory<float>>(records, cancellationToken, out var floatTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = await floatTask.ConfigureAwait(false);
            }
            else if (vectorProperty.TryGenerateEmbeddings<TRecord, Embedding<double>, ReadOnlyMemory<double>>(records, cancellationToken, out var doubleTask))
            {
                generatedEmbeddings ??= new IReadOnlyList<Embedding>?[vectorPropertyCount];
                generatedEmbeddings[i] = await doubleTask.ConfigureAwait(false);
            }
            else
            {
                throw new InvalidOperationException(
                    $"The embedding generator configured on property '{vectorProperty.ModelName}' cannot produce an embedding of type '{typeof(Embedding<float>).Name}' for the given input type.");
            }
        }

        return (records, generatedEmbeddings);
    }
}

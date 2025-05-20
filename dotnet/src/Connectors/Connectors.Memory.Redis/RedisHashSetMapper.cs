// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Class for mapping between a hashset stored in redis, and the consumer data model.
/// </summary>
/// <typeparam name="TConsumerDataModel">The consumer data model to map to or from.</typeparam>
internal sealed class RedisHashSetMapper<TConsumerDataModel>(CollectionModel model)
{
    /// <inheritdoc />
    public (string Key, HashEntry[] HashEntries) MapFromDataToStorageModel(TConsumerDataModel dataModel, int recordIndex, IReadOnlyList<Embedding>?[]? generatedEmbeddings)
    {
        var keyValue = model.KeyProperty.GetValueAsObject(dataModel!) as string ??
            throw new InvalidOperationException($"Missing key property {model.KeyProperty.ModelName} on provided record of type '{typeof(TConsumerDataModel).Name}'.");

        var hashEntries = new List<HashEntry>();
        foreach (var property in model.DataProperties)
        {
            var value = property.GetValueAsObject(dataModel!);
            hashEntries.Add(new HashEntry(property.StorageName, RedisValue.Unbox(value)));
        }

        for (var i = 0; i < model.VectorProperties.Count; i++)
        {
            var property = model.VectorProperties[i];

            var value = generatedEmbeddings?[i]?[recordIndex] ?? property.GetValueAsObject(dataModel!);

            if (value is not null)
            {
                // Convert the vector to a byte array and store it in the hash entry.
                // We only support float and double vectors and we do checking in the
                // collection constructor to ensure that the model has no other vector types.
                hashEntries.Add(new HashEntry(property.StorageName, value switch
                {
                    ReadOnlyMemory<float> m => MemoryMarshal.AsBytes(m.Span).ToArray(),
                    Embedding<float> e => MemoryMarshal.AsBytes(e.Vector.Span).ToArray(),
                    float[] a => MemoryMarshal.AsBytes(a.AsSpan()).ToArray(),

                    ReadOnlyMemory<double> m => MemoryMarshal.AsBytes(m.Span).ToArray(),
                    Embedding<double> e => MemoryMarshal.AsBytes(e.Vector.Span).ToArray(),
                    double[] a => MemoryMarshal.AsBytes(a.AsSpan()).ToArray(),

                    _ => throw new InvalidOperationException($"Unsupported vector type '{value.GetType()}'. Only float and double vectors are supported.")
                }));
            }
        }

        return (keyValue, hashEntries.ToArray());
    }

    /// <inheritdoc />
    public TConsumerDataModel MapFromStorageToDataModel((string Key, HashEntry[] HashEntries) storageModel, bool includeVectors)
    {
        var hashEntriesDictionary = storageModel.HashEntries.ToDictionary(x => (string)x.Name!, x => x.Value);

        // Construct the output record.
        var outputRecord = model.CreateRecord<TConsumerDataModel>()!;

        // Set Key.
        model.KeyProperty.SetValueAsObject(outputRecord, storageModel.Key);

        // Set each vector property if embeddings should be returned.
        if (includeVectors)
        {
            foreach (var property in model.VectorProperties)
            {
                if (hashEntriesDictionary.TryGetValue(property.StorageName, out var value))
                {
                    if (value.IsNull)
                    {
                        property.SetValueAsObject(outputRecord!, null);
                        continue;
                    }

                    var vector = (byte[])value!;

                    property.SetValueAsObject(outputRecord!, (Nullable.GetUnderlyingType(property.Type) ?? property.Type) switch
                    {
                        Type t when t == typeof(ReadOnlyMemory<float>)
                            => new ReadOnlyMemory<float>(MemoryMarshal.Cast<byte, float>(vector).ToArray()),
                        Type t when t == typeof(Embedding<float>)
                            => new Embedding<float>(MemoryMarshal.Cast<byte, float>(vector).ToArray()),
                        Type t when t == typeof(float[])
                            => MemoryMarshal.Cast<byte, float>(vector).ToArray(),

                        Type t when t == typeof(ReadOnlyMemory<double>)
                            => new ReadOnlyMemory<double>(MemoryMarshal.Cast<byte, double>(vector).ToArray()),
                        Type t when t == typeof(Embedding<double>)
                            => new Embedding<double>(MemoryMarshal.Cast<byte, double>(vector).ToArray()),
                        Type t when t == typeof(double[])
                            => MemoryMarshal.Cast<byte, double>(vector).ToArray(),

                        _ => throw new InvalidOperationException($"Unsupported vector type '{property.Type}'. Only float and double vectors are supported.")
                    });
                }
            }
        }

        foreach (var property in model.DataProperties)
        {
            if (hashEntriesDictionary.TryGetValue(property.StorageName, out var hashValue))
            {
                if (hashValue.IsNull)
                {
                    property.SetValueAsObject(outputRecord!, null);
                    continue;
                }

                var typeOrNullableType = Nullable.GetUnderlyingType(property.Type) ?? property.Type;
                var value = Convert.ChangeType(hashValue, typeOrNullableType);
                property.SetValueAsObject(outputRecord!, value);
            }
        }

        return outputRecord;
    }
}

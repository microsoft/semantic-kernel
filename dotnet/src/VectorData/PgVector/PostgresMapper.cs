// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;
using Npgsql;

namespace Microsoft.SemanticKernel.Connectors.PgVector;

/// <summary>
/// A mapper class that handles the conversion between data models and storage models for Postgres vector store.
/// </summary>
/// <typeparam name="TRecord">The type of the data model record.</typeparam>
internal sealed class PostgresMapper<TRecord>(CollectionModel model)
    where TRecord : class
{
    public TRecord MapFromStorageToDataModel(NpgsqlDataReader reader, bool includeVectors)
    {
        var record = model.CreateRecord<TRecord>()!;

        PopulateProperty(model.KeyProperty, reader, record);

        foreach (var dataProperty in model.DataProperties)
        {
            PopulateProperty(dataProperty, reader, record);
        }

        if (includeVectors)
        {
            foreach (var vectorProperty in model.VectorProperties)
            {
                int ordinal = reader.GetOrdinal(vectorProperty.StorageName);

                if (reader.IsDBNull(ordinal))
                {
                    vectorProperty.SetValueAsObject(record, null);
                    continue;
                }

                switch (reader.GetValue(ordinal))
                {
                    case Pgvector.Vector { Memory: ReadOnlyMemory<float> memory }:
                    {
                        vectorProperty.SetValueAsObject(record, (Nullable.GetUnderlyingType(vectorProperty.Type) ?? vectorProperty.Type) switch
                        {
                            var t when t == typeof(ReadOnlyMemory<float>) => memory,
                            var t when t == typeof(Embedding<float>) => new Embedding<float>(memory),
                            var t when t == typeof(float[])
                                => MemoryMarshal.TryGetArray(memory, out ArraySegment<float> segment) && segment.Count == segment.Array!.Length
                                    ? segment.Array
                                    : memory.ToArray(),

                            _ => throw new UnreachableException()
                        });
                        continue;
                    }

#if NET8_0_OR_GREATER
                    case Pgvector.HalfVector { Memory: ReadOnlyMemory<Half> memory }:
                    {
                        vectorProperty.SetValueAsObject(record, (Nullable.GetUnderlyingType(vectorProperty.Type) ?? vectorProperty.Type) switch
                        {
                            var t when t == typeof(ReadOnlyMemory<Half>) => memory,
                            var t when t == typeof(Embedding<Half>) => new Embedding<Half>(memory),
                            var t when t == typeof(Half[])
                                => MemoryMarshal.TryGetArray(memory, out ArraySegment<Half> segment) && segment.Count == segment.Array!.Length
                                    ? segment.Array
                                    : memory.ToArray(),

                            _ => throw new UnreachableException()
                        });
                        continue;
                    }
#endif

                    case BitArray bitArray when vectorProperty.Type == typeof(BinaryEmbedding):
                        vectorProperty.SetValueAsObject(record, new BinaryEmbedding(bitArray));
                        continue;

                    case BitArray bitArray:
                        vectorProperty.SetValueAsObject(record, bitArray);
                        continue;

                    case Pgvector.SparseVector pgSparseVector:
                        vectorProperty.SetValueAsObject(record, pgSparseVector);
                        continue;

                    // TODO: We currently allow round-tripping null for the vector property; this is not supported for most (?) dedicated databases; think about it.
                    case null:
                        vectorProperty.SetValueAsObject(record, null);
                        continue;

                    case var value:
                        throw new InvalidOperationException($"Embedding vector read back from PostgreSQL is of type '{value.GetType().Name}' instead of the expected Pgvector.Vector type for property '{vectorProperty.ModelName}'.");
                }
            }
        }

        return record;
    }

    private static void PopulateProperty(PropertyModel property, NpgsqlDataReader reader, TRecord record)
    {
        int ordinal = reader.GetOrdinal(property.StorageName);

        if (reader.IsDBNull(ordinal))
        {
            property.SetValueAsObject(record, null);
            return;
        }

        var type = Nullable.GetUnderlyingType(property.Type) ?? property.Type;

        // First try an efficient switch over the TypeCode enum for common base types
        switch (Type.GetTypeCode(type))
        {
            case TypeCode.Int32:
                property.SetValue(record, reader.GetInt32(ordinal));
                return;
            case TypeCode.String:
                property.SetValue(record, reader.GetString(ordinal));
                return;
            case TypeCode.Boolean:
                property.SetValue(record, reader.GetBoolean(ordinal));
                return;
            case TypeCode.Int16:
                property.SetValue(record, reader.GetInt16(ordinal));
                return;
            case TypeCode.Int64:
                property.SetValue(record, reader.GetInt64(ordinal));
                return;
            case TypeCode.Single:
                property.SetValue(record, reader.GetFloat(ordinal));
                return;
            case TypeCode.Double:
                property.SetValue(record, reader.GetDouble(ordinal));
                return;
            case TypeCode.Decimal:
                property.SetValue(record, reader.GetDecimal(ordinal));
                return;
            case TypeCode.DateTime:
                property.SetValue(record, reader.GetDateTime(ordinal));
                return;

            case TypeCode.Object:
                switch (type)
                {
                    // Some more base types
                    case var t when t == typeof(Guid):
                        property.SetValue(record, reader.GetGuid(ordinal));
                        return;
                    case var t when t == typeof(DateTimeOffset):
                        property.SetValue(record, reader.GetFieldValue<DateTimeOffset>(ordinal));
                        return;
                    case var t when t == typeof(byte[]):
                        property.SetValue(record, reader.GetFieldValue<byte[]>(ordinal));
                        return;

                    // Array types are returned by default from GetValue(), and since they're reference types
                    // there's no boxing involved.
                    case var t when t.IsArray:
                        property.SetValueAsObject(record, reader.GetValue(ordinal));
                        return;

                    // For List<T>, we need to call GetFieldValue<List<T>>() to get the right type
                    case Type lt when lt.IsGenericType && lt.GetGenericTypeDefinition() == typeof(List<>):
                        switch (type)
                        {
                            case Type t when t == typeof(List<int>):
                                property.SetValueAsObject(record, reader.GetFieldValue<List<int>>(ordinal));
                                return;
                            case Type t when t == typeof(List<string>):
                                property.SetValueAsObject(record, reader.GetFieldValue<List<string>>(ordinal));
                                return;
                            case Type t when t == typeof(List<bool>):
                                property.SetValueAsObject(record, reader.GetFieldValue<List<bool>>(ordinal));
                                return;
                            case Type t when t == typeof(List<short>):
                                property.SetValueAsObject(record, reader.GetFieldValue<List<short>>(ordinal));
                                return;
                            case Type t when t == typeof(List<long>):
                                property.SetValueAsObject(record, reader.GetFieldValue<List<long>>(ordinal));
                                return;
                            case Type t when t == typeof(List<float>):
                                property.SetValueAsObject(record, reader.GetFieldValue<List<float>>(ordinal));
                                return;
                            case Type t when t == typeof(List<double>):
                                property.SetValueAsObject(record, reader.GetFieldValue<List<double>>(ordinal));
                                return;
                            case Type t when t == typeof(List<decimal>):
                                property.SetValueAsObject(record, reader.GetFieldValue<List<decimal>>(ordinal));
                                return;
                            case Type t when t == typeof(List<DateTime>):
                                property.SetValueAsObject(record, reader.GetFieldValue<List<DateTime>>(ordinal));
                                return;
                            case Type t when t == typeof(List<Guid>):
                                property.SetValueAsObject(record, reader.GetFieldValue<List<Guid>>(ordinal));
                                return;
                            case Type t when t == typeof(List<DateTimeOffset>):
                                property.SetValueAsObject(record, reader.GetFieldValue<List<DateTimeOffset>>(ordinal));
                                return;
                            case Type t when t == typeof(List<byte[]>):
                                property.SetValueAsObject(record, reader.GetFieldValue<List<byte[]>>(ordinal));
                                return;
                            default:
                                throw new UnreachableException("Unsupported property type: " + property.Type.Name);
                        }

                    default:
                        throw new UnreachableException("Unsupported property type: " + property.Type.Name);
                }

            default:
                throw new UnreachableException("Unsupported property type: " + property.Type.Name);
        }
    }
}

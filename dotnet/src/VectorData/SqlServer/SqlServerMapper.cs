// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Text.Json;
using Microsoft.Data.SqlClient;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.SqlServer;

internal sealed class SqlServerMapper<TRecord>(CollectionModel model)
{
    public TRecord MapFromStorageToDataModel(SqlDataReader reader, bool includeVectors)
    {
        var record = model.CreateRecord<TRecord>()!;

        PopulateValue(reader, model.KeyProperty, record);

        foreach (var property in model.DataProperties)
        {
            PopulateValue(reader, property, record);
        }

        if (includeVectors)
        {
            foreach (var property in model.VectorProperties)
            {
                try
                {
                    var ordinal = reader.GetOrdinal(property.StorageName);

                    if (!reader.IsDBNull(ordinal))
                    {
                        // TODO: For now, SQL Server provides access to vectors as JSON arrays, but the plan is to switch
                        // to an efficient binary format in the future.
                        var vectorArray = JsonSerializer.Deserialize<float[]>(reader.GetString(ordinal), SqlServerJsonSerializerContext.Default.SingleArray);

                        property.SetValueAsObject(record, property.Type switch
                        {
                            var t when t == typeof(ReadOnlyMemory<float>) => new ReadOnlyMemory<float>(vectorArray),
                            var t when t == typeof(Embedding<float>) => new Embedding<float>(vectorArray),
                            var t when t == typeof(float[]) => vectorArray,

                            _ => throw new UnreachableException()
                        });
                    }
                }
                catch (Exception e)
                {
                    throw new InvalidOperationException($"Failed to deserialize vector property '{property.ModelName}'.", e);
                }
            }
        }

        return record;

        static void PopulateValue(SqlDataReader reader, PropertyModel property, object record)
        {
            try
            {
                var ordinal = reader.GetOrdinal(property.StorageName);

                if (reader.IsDBNull(ordinal))
                {
                    property.SetValueAsObject(record, null);
                    return;
                }

                switch (property.Type)
                {
                    case var t when t == typeof(byte):
                        property.SetValue(record, reader.GetByte(ordinal)); // TINYINT
                        break;
                    case var t when t == typeof(short):
                        property.SetValue(record, reader.GetInt16(ordinal)); // SMALLINT
                        break;
                    case var t when t == typeof(int):
                        property.SetValue(record, reader.GetInt32(ordinal)); // INT
                        break;
                    case var t when t == typeof(long):
                        property.SetValue(record, reader.GetInt64(ordinal)); // BIGINT
                        break;

                    case var t when t == typeof(float):
                        property.SetValue(record, reader.GetFloat(ordinal)); // REAL
                        break;
                    case var t when t == typeof(double):
                        property.SetValue(record, reader.GetDouble(ordinal)); // FLOAT
                        break;
                    case var t when t == typeof(decimal):
                        property.SetValue(record, reader.GetDecimal(ordinal)); // DECIMAL
                        break;

                    case var t when t == typeof(string):
                        property.SetValue(record, reader.GetString(ordinal)); // NVARCHAR
                        break;
                    case var t when t == typeof(Guid):
                        property.SetValue(record, reader.GetGuid(ordinal)); // UNIQUEIDENTIFIER
                        break;
                    case var t when t == typeof(byte[]):
                        property.SetValueAsObject(record, reader.GetValue(ordinal)); // VARBINARY
                        break;
                    case var t when t == typeof(bool):
                        property.SetValue(record, reader.GetBoolean(ordinal)); // BIT
                        break;

                    case var t when t == typeof(DateTime):
                        property.SetValue(record, reader.GetDateTime(ordinal)); // DATETIME2
                        break;

#if NET
                    case var t when t == typeof(TimeOnly):
                        property.SetValue(record, reader.GetFieldValue<TimeOnly>(ordinal)); // TIME
                        break;
#endif

                    default:
                        throw new NotSupportedException($"Unsupported type '{property.Type.Name}' for property '{property.ModelName}'.");
                }
            }
            catch (Exception ex)
            {
                throw new InvalidOperationException($"Failed to read property '{property.ModelName}' of type '{property.Type.Name}'.", ex);
            }
        }
    }
}

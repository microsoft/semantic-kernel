// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Data;
using Qdrant.Client.Grpc;

namespace Microsoft.SemanticKernel.Connectors.Qdrant;

/// <summary>
/// Mapper between a Qdrant record and the consumer data model that uses json as an intermediary to allow supporting a wide range of models.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class QdrantVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, PointStruct>
    where TRecord : class
{
    /// <summary>A set of types that data properties on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedDataTypes =
    [
        typeof(string),
        typeof(int),
        typeof(long),
        typeof(double),
        typeof(float),
        typeof(bool),
        typeof(int?),
        typeof(long?),
        typeof(double?),
        typeof(float?),
        typeof(bool?)
    ];

    /// <summary>A set of types that vectors on the provided model may have.</summary>
    /// <remarks>
    /// While qdrant supports float32 and uint64, the api only supports float64, therefore
    /// any float32 vectors will be converted to float64 before being sent to qdrant.
    /// </remarks>
    private static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?),
        typeof(ReadOnlyMemory<double>),
        typeof(ReadOnlyMemory<double>?)
    ];

    /// <summary>A property info object that points at the key property for the current model, allowing easy reading and writing of this property.</summary>
    private readonly PropertyInfo _keyPropertyInfo;

    /// <summary>A list of property info objects that point at the data properties in the current model, and allows easy reading and writing of these properties.</summary>
    private readonly List<PropertyInfo> _dataPropertiesInfo;

    /// <summary>A list of property info objects that point at the vector properties in the current model, and allows easy reading and writing of these properties.</summary>
    private readonly List<PropertyInfo> _vectorPropertiesInfo;

    /// <summary>A dictionary that maps from a property name to the configured name that should be used when storing it.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames;

    /// <summary>A dictionary that maps from a property name to the configured name that should be used when serializing it to json.</summary>
    private readonly Dictionary<string, string> _jsonPropertyNames = new();
    /// <summary>A helper to access property information for the current data model and record definition.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>A value indicating whether the vectors in the store are named, or whether there is just a single unnamed vector per qdrant point.</summary>
    private readonly bool _hasNamedVectors;

    /// <summary>
    /// Initializes a new instance of the <see cref="QdrantVectorStoreRecordMapper{TDataModel}"/> class.
    /// </summary>
    /// <param name="propertyReader">A helper to access property information for the current data model and record definition.</param>
    /// <param name="hasNamedVectors">A value indicating whether the vectors in the store are named, or whether there is just a single unnamed vector per qdrant point.</param>
    public QdrantVectorStoreRecordMapper(
        VectorStoreRecordPropertyReader propertyReader,
        bool hasNamedVectors)
    {
        Verify.NotNull(propertyReader);

        // Validate property types.
        var propertiesInfo = VectorStoreRecordPropertyReader.FindProperties(typeof(TRecord), vectorStoreRecordDefinition, supportsMultipleVectors: hasNamedVectors);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(propertiesInfo.DataProperties, QdrantVectorStoreRecordFieldMapping.s_supportedDataTypes, "Data", supportEnumerable: true);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(propertiesInfo.VectorProperties, QdrantVectorStoreRecordFieldMapping.s_supportedVectorTypes, "Vector");
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(propertiesInfo.DataProperties, s_supportedDataTypes, "Data", supportEnumerable: true);
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(propertiesInfo.VectorProperties, s_supportedVectorTypes, "Vector");
        propertyReader.VerifyHasParameterlessConstructor();
        propertyReader.VerifyDataProperties(QdrantVectorStoreRecordFieldMapping.s_supportedDataTypes, supportEnumerable: true);
        propertyReader.VerifyVectorProperties(QdrantVectorStoreRecordFieldMapping.s_supportedVectorTypes);

        // Assign.
        this._propertyReader = propertyReader;
        this._hasNamedVectors = hasNamedVectors;
    }

    /// <inheritdoc />
    public PointStruct MapFromDataToStorageModel(TRecord dataModel)
    {
        PointId pointId;
        var keyPropertyInfo = this._propertyReader.KeyPropertyInfo;
        if (keyPropertyInfo.PropertyType == typeof(ulong))
        {
            var key = keyPropertyInfo.GetValue(dataModel) as ulong? ?? throw new VectorStoreRecordMappingException($"Missing key property {keyPropertyInfo.Name} on provided record of type {typeof(TRecord).FullName}.");
            pointId = new PointId { Num = key };
        }
        else if (keyPropertyInfo.PropertyType == typeof(Guid))
        {
            var key = keyPropertyInfo.GetValue(dataModel) as Guid? ?? throw new VectorStoreRecordMappingException($"Missing key property {keyPropertyInfo.Name} on provided record of type {typeof(TRecord).FullName}.");
            pointId = new PointId { Uuid = key.ToString("D") };
        }
        else
        {
            throw new VectorStoreRecordMappingException($"Unsupported key type {keyPropertyInfo.PropertyType.FullName} for key property {keyPropertyInfo.Name} on provided record of type {typeof(TRecord).FullName}.");
        }

        // Create point.
        var pointStruct = new PointStruct
        {
            Id = pointId,
            Vectors = new Vectors(),
            Payload = { },
        };

        // Add point payload.
        foreach (var dataPropertyInfo in this._propertyReader.DataPropertiesInfo)
        {
            var propertyName = this._propertyReader.GetStoragePropertyName(dataPropertyInfo.Name);
            var propertyValue = dataPropertyInfo.GetValue(dataModel);
            pointStruct.Payload.Add(propertyName, QdrantVectorStoreRecordFieldMapping.ConvertToGrpcFieldValue(propertyValue));
            pointStruct.Payload.Add(propertyName, ConvertToGrpcFieldValue(propertyValue));
        }

        // Add vectors.
        if (this._hasNamedVectors)
        {
            var namedVectors = new NamedVectors();
            foreach (var vectorPropertyInfo in this._propertyReader.VectorPropertiesInfo)
            {
                var propertyName = this._propertyReader.GetStoragePropertyName(vectorPropertyInfo.Name);
                var propertyValue = vectorPropertyInfo.GetValue(dataModel);
                if (propertyValue is not null)
                {
                    var castPropertyValue = (ReadOnlyMemory<float>)propertyValue;
                    namedVectors.Vectors.Add(propertyName, castPropertyValue.ToArray());
                }
            }

            pointStruct.Vectors.Vectors_ = namedVectors;
        }
        else
        {
            // We already verified in the constructor via FindProperties that there is exactly one vector property when not using named vectors.
            var vectorPropertyInfo = this._propertyReader.FirstVectorPropertyInfo!;
            if (vectorPropertyInfo.GetValue(dataModel) is ReadOnlyMemory<float> floatROM)
            {
                pointStruct.Vectors.Vector = floatROM.ToArray();
            }
            else
            {
                throw new VectorStoreRecordMappingException($"Vector property {vectorPropertyInfo.Name} on provided record of type {typeof(TRecord).FullName} may not be null when not using named vectors.");
            }
        }

        return pointStruct;
    }

    /// <inheritdoc />
    public TRecord MapFromStorageToDataModel(PointStruct storageModel, StorageToDataModelMapperOptions options)
    {
        // Get the key property name and value.
        var keyPropertyValue = storageModel.Id.HasNum ? storageModel.Id.Num as object : new Guid(storageModel.Id.Uuid) as object;

        // Construct the output record.
        var outputRecord = (TRecord)this._propertyReader.ParameterLessConstructorInfo.Invoke(null);

        // Set Key.
        this._propertyReader.KeyPropertyInfo.SetValue(outputRecord, keyPropertyValue);

        // Set each vector property if embeddings are included in the point.
        if (options?.IncludeVectors is true)
        {
            if (this._hasNamedVectors)
            {
                VectorStoreRecordMapping.SetValuesOnProperties(
                    outputRecord,
                    this._propertyReader.VectorPropertiesInfo,
                    this._propertyReader.StoragePropertyNamesMap,
                    storageModel.Vectors.Vectors_.Vectors,
                    (Vector vector, Type targetType) => new ReadOnlyMemory<float>(vector.Data.ToArray()));
            }
            else
            {
                outputJsonObject.Add(jsonName, QdrantVectorStoreRecordFieldMapping.ConvertFromGrpcFieldValueToJsonNode(value));
                outputJsonObject.Add(jsonName, ConvertFromGrpcFieldValueToJsonNode(value));
                var propertyInfoWithValue = new KeyValuePair<PropertyInfo, object?>(
                        this._propertyReader.FirstVectorPropertyInfo!,
                        new ReadOnlyMemory<float>(storageModel.Vectors.Vector.Data.ToArray()));
                VectorStoreRecordMapping.SetPropertiesOnRecord(
                this._propertyReader.FirstVectorPropertyInfo!.SetValue(
                    outputRecord,
                    new ReadOnlyMemory<float>(storageModel.Vectors.Vector.Data.ToArray()));
            }
        }

        // Set each data property.
        VectorStoreRecordMapping.SetValuesOnProperties(
            outputRecord,
            this._propertyReader.DataPropertiesInfo,
            this._propertyReader.StoragePropertyNamesMap,
            storageModel.Payload,
            QdrantVectorStoreRecordFieldMapping.ConvertFromGrpcFieldValueToNativeType);

        return outputRecord;
    }

    /// <summary>
    /// Convert the given <paramref name="payloadValue"/> to the correct native type based on its properties.
    /// </summary>
    /// <param name="payloadValue">The value to convert to a native type.</param>
    /// <returns>The converted native value.</returns>
    /// <exception cref="VectorStoreRecordMappingException">Thrown when an unsupported type is encountered.</exception>
    private static JsonNode? ConvertFromGrpcFieldValueToJsonNode(Value payloadValue)
    {
        return payloadValue.KindCase switch
        {
            Value.KindOneofCase.NullValue => null,
            Value.KindOneofCase.IntegerValue => JsonValue.Create(payloadValue.IntegerValue),
            Value.KindOneofCase.StringValue => JsonValue.Create(payloadValue.StringValue),
            Value.KindOneofCase.DoubleValue => JsonValue.Create(payloadValue.DoubleValue),
            Value.KindOneofCase.BoolValue => JsonValue.Create(payloadValue.BoolValue),
            Value.KindOneofCase.ListValue => new JsonArray(payloadValue.ListValue.Values.Select(x => ConvertFromGrpcFieldValueToJsonNode(x)).ToArray()),
            Value.KindOneofCase.StructValue => new JsonObject(payloadValue.StructValue.Fields.ToDictionary(x => x.Key, x => ConvertFromGrpcFieldValueToJsonNode(x.Value))),
            _ => throw new VectorStoreRecordMappingException($"Unsupported grpc value kind {payloadValue.KindCase}."),
        };
    }

    /// <summary>
    /// Convert the given <paramref name="sourceValue"/> to a <see cref="Value"/> object that can be stored in Qdrant.
    /// </summary>
    /// <param name="sourceValue">The object to convert.</param>
    /// <returns>The converted Qdrant value.</returns>
    /// <exception cref="VectorStoreRecordMappingException">Thrown when an unsupported type is encountered.</exception>
    private static Value ConvertToGrpcFieldValue(object? sourceValue)
    {
        var value = new Value();
        if (sourceValue is null)
        {
            value.NullValue = NullValue.NullValue;
        }
        else if (sourceValue is int intValue)
        {
            value.IntegerValue = intValue;
        }
        else if (sourceValue is long longValue)
        {
            value.IntegerValue = longValue;
        }
        else if (sourceValue is string stringValue)
        {
            value.StringValue = stringValue;
        }
        else if (sourceValue is float floatValue)
        {
            value.DoubleValue = floatValue;
        }
        else if (sourceValue is double doubleValue)
        {
            value.DoubleValue = doubleValue;
        }
        else if (sourceValue is bool boolValue)
        {
            value.BoolValue = boolValue;
        }
        else if (sourceValue is IEnumerable<int> ||
            sourceValue is IEnumerable<long> ||
            sourceValue is IEnumerable<string> ||
            sourceValue is IEnumerable<float> ||
            sourceValue is IEnumerable<double> ||
            sourceValue is IEnumerable<bool>)
        {
            var listValue = sourceValue as IEnumerable;
            value.ListValue = new ListValue();
            foreach (var item in listValue!)
            {
                value.ListValue.Values.Add(ConvertToGrpcFieldValue(item));
            }
        }
        else
        {
            throw new VectorStoreRecordMappingException($"Unsupported source value type {sourceValue?.GetType().FullName}.");
        }

        return value;
    }
}

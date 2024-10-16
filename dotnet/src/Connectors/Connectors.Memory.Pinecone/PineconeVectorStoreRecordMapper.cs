// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData;
using Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Mapper between a Pinecone record and the consumer data model that uses json as an intermediary to allow supporting a wide range of models.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class PineconeVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, Vector>
{
    /// <summary>A set of types that a key on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedKeyTypes = [typeof(string)];

    /// <summary>A set of types that data properties on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedDataTypes =
    [
        typeof(bool),
        typeof(bool?),
        typeof(string),
        typeof(int),
        typeof(int?),
        typeof(long),
        typeof(long?),
        typeof(float),
        typeof(float?),
        typeof(double),
        typeof(double?),
        typeof(decimal),
        typeof(decimal?),
    ];

    /// <summary>A set of types that enumerable data properties on the provided model may use as their element types.</summary>
    private static readonly HashSet<Type> s_supportedEnumerableDataElementTypes =
    [
        typeof(string)
    ];

    /// <summary>A set of types that vectors on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?),
    ];

    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeVectorStoreRecordMapper{TDataModel}"/> class.
    /// </summary>
    /// <param name="propertyReader">A helper to access property information for the current data model and record definition.</param>
    public PineconeVectorStoreRecordMapper(
        VectorStoreRecordPropertyReader propertyReader)
    {
        // Validate property types.
        propertyReader.VerifyHasParameterlessConstructor();
        propertyReader.VerifyKeyProperties(s_supportedKeyTypes);
        propertyReader.VerifyDataProperties(s_supportedDataTypes, s_supportedEnumerableDataElementTypes);
        propertyReader.VerifyVectorProperties(s_supportedVectorTypes);

        // Assign.
        this._propertyReader = propertyReader;
    }

    /// <inheritdoc />
    public Vector MapFromDataToStorageModel(TRecord dataModel)
    {
        var keyObject = this._propertyReader.KeyPropertyInfo.GetValue(dataModel);
        if (keyObject is null)
        {
            throw new VectorStoreRecordMappingException($"Key property {this._propertyReader.KeyPropertyName} on provided record of type {typeof(TRecord).FullName} may not be null.");
        }

        var metadata = new MetadataMap();
        foreach (var dataPropertyInfo in this._propertyReader.DataPropertiesInfo)
        {
            var propertyName = this._propertyReader.GetStoragePropertyName(dataPropertyInfo.Name);
            var propertyValue = dataPropertyInfo.GetValue(dataModel);
            if (propertyValue != null)
            {
                metadata[propertyName] = ConvertToMetadataValue(propertyValue);
            }
        }

        var valuesObject = this._propertyReader.FirstVectorPropertyInfo!.GetValue(dataModel);
        if (valuesObject is not ReadOnlyMemory<float> values)
        {
            throw new VectorStoreRecordMappingException($"Vector property {this._propertyReader.FirstVectorPropertyName} on provided record of type {typeof(TRecord).FullName} may not be null.");
        }

        // TODO: what about sparse values?
        var result = new Vector
        {
            Id = (string)keyObject,
            Values = values.ToArray(),
            Metadata = metadata,
            SparseValues = null
        };

        return result;
    }

    /// <inheritdoc />
    public TRecord MapFromStorageToDataModel(Vector storageModel, StorageToDataModelMapperOptions options)
    {
        // Construct the output record.
        var outputRecord = (TRecord)this._propertyReader.ParameterLessConstructorInfo.Invoke(null);

        // Set Key.
        this._propertyReader.KeyPropertyInfo.SetValue(outputRecord, storageModel.Id);

        // Set Vector.
        if (options?.IncludeVectors is true)
        {
            this._propertyReader.FirstVectorPropertyInfo!.SetValue(
                outputRecord,
                new ReadOnlyMemory<float>(storageModel.Values));
        }

        // Set Data.
        if (storageModel.Metadata != null)
        {
            VectorStoreRecordMapping.SetValuesOnProperties(
                outputRecord,
                this._propertyReader.DataPropertiesInfo,
                this._propertyReader.StoragePropertyNamesMap,
                storageModel.Metadata,
                ConvertFromMetadataValueToNativeType);
        }

        return outputRecord;
    }

    private static object? ConvertFromMetadataValueToNativeType(MetadataValue metadataValue, Type targetType)
        => metadataValue.Inner switch
        {
            null => null,
            bool boolValue => boolValue,
            string stringValue => stringValue,
            // Numeric values are not always coming from the SDK in the desired type
            // that the data model requires, so we need to convert them.
            int intValue => ConvertToNumericValue(intValue, targetType),
            long longValue => ConvertToNumericValue(longValue, targetType),
            float floatValue => ConvertToNumericValue(floatValue, targetType),
            double doubleValue => ConvertToNumericValue(doubleValue, targetType),
            decimal decimalValue => ConvertToNumericValue(decimalValue, targetType),
            MetadataValue[] array => VectorStoreRecordMapping.CreateEnumerable(array.Select(x => ConvertFromMetadataValueToNativeType(x, VectorStoreRecordPropertyVerification.GetCollectionElementType(targetType))), targetType),
            List<MetadataValue> list => VectorStoreRecordMapping.CreateEnumerable(list.Select(x => ConvertFromMetadataValueToNativeType(x, VectorStoreRecordPropertyVerification.GetCollectionElementType(targetType))), targetType),
            _ => throw new VectorStoreRecordMappingException($"Unsupported metadata type: '{metadataValue.Inner?.GetType().FullName}'."),
        };

    private static object? ConvertToNumericValue(object? number, Type targetType)
    {
        if (number is null)
        {
            return null;
        }

        return targetType switch
        {
            Type intType when intType == typeof(int) || intType == typeof(int?) => Convert.ToInt32(number),
            Type longType when longType == typeof(long) || longType == typeof(long?) => Convert.ToInt64(number),
            Type floatType when floatType == typeof(float) || floatType == typeof(float?) => Convert.ToSingle(number),
            Type doubleType when doubleType == typeof(double) || doubleType == typeof(double?) => Convert.ToDouble(number),
            Type decimalType when decimalType == typeof(decimal) || decimalType == typeof(decimal?) => Convert.ToDecimal(number),
            _ => throw new VectorStoreRecordMappingException($"Unsupported target numeric type '{targetType.FullName}'."),
        };
    }

    // TODO: take advantage of MetadataValue.TryCreate once we upgrade the version of Pinecone.NET
    private static MetadataValue ConvertToMetadataValue(object? sourceValue)
        => sourceValue switch
        {
            bool boolValue => boolValue,
            string stringValue => stringValue,
            int intValue => intValue,
            long longValue => longValue,
            float floatValue => floatValue,
            double doubleValue => doubleValue,
            decimal decimalValue => decimalValue,
            string[] stringArray => stringArray,
            List<string> stringList => stringList,
            IEnumerable<string> stringEnumerable => stringEnumerable.ToArray(),
            _ => throw new VectorStoreRecordMappingException($"Unsupported source value type '{sourceValue?.GetType().FullName}'.")
        };
}

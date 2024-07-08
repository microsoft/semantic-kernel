// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Data;
using Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Mapper between a Pinecone record and the consumer data model that uses json as an intermediary to allow supporting a wide range of models.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class PineconeVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, Vector>
    where TRecord : class
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
        typeof(string[]),
        typeof(List<string>),
    ];

    /// <summary>A set of types that vectors on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?),
    ];

    /// <summary>A list of property info objects that point at the payload properties in the current model, and allows easy reading and writing of these properties.</summary>
    private readonly List<PropertyInfo> _payloadPropertiesInfo = [];

    /// <summary>A property info object that points at the vector property in the current model, and allows easy reading and writing of this property.</summary>
    private readonly PropertyInfo _vectorPropertyInfo;

    /// <summary>A property info object that points at the key property for the current model, allowing easy reading and writing of this property.</summary>
    private readonly PropertyInfo _keyPropertyInfo;

    /// <summary>A dictionary that maps from a property name to the configured name that should be used when storing it.</summary>
    private readonly Dictionary<string, string> _storagePropertyNames = [];

    /// <summary>Configuration options for this class.</summary>
    private readonly PineconeVectorStoreRecordMapperOptions _options;

    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeVectorStoreRecordMapper{TDataModel}"/> class.
    /// </summary>
    /// <param name="options">Options to use when doing the model conversion.</param>
    public PineconeVectorStoreRecordMapper(PineconeVectorStoreRecordMapperOptions options)
    {
        Verify.NotNull(options);
        this._options = options;

        (PropertyInfo keyProperty, List<PropertyInfo> dataProperties, List<PropertyInfo> vectorProperties) properties;
        if (this._options.VectorStoreRecordDefinition is not null)
        {
            properties = VectorStoreRecordPropertyReader.FindProperties(typeof(TRecord), this._options.VectorStoreRecordDefinition, supportsMultipleVectors: false);
        }
        else
        {
            properties = VectorStoreRecordPropertyReader.FindProperties(typeof(TRecord), supportsMultipleVectors: false);
        }

        VectorStoreRecordPropertyReader.VerifyPropertyTypes([properties.keyProperty], s_supportedKeyTypes, "Key");
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.dataProperties, s_supportedDataTypes, "Data");
        VectorStoreRecordPropertyReader.VerifyPropertyTypes(properties.vectorProperties, s_supportedVectorTypes, "Vector");

        this._keyPropertyInfo = properties.keyProperty;
        this._payloadPropertiesInfo = properties.dataProperties;
        this._vectorPropertyInfo = properties.vectorProperties.First();
        this._storagePropertyNames = VectorStoreRecordPropertyReader.BuildPropertyNameToStorageNameMap(properties, this._options.VectorStoreRecordDefinition);
    }

    /// <inheritdoc />
    public Vector MapFromDataToStorageModel(TRecord dataModel)
    {
        var keyObject = this._keyPropertyInfo.GetValue(dataModel);
        if (keyObject is null)
        {
            throw new VectorStoreRecordMappingException($"Key property {this._keyPropertyInfo.Name} on provided record of type {typeof(TRecord).FullName} may not be null.");
        }

        var metadata = new MetadataMap();
        foreach (var payloadPropertyInfo in this._payloadPropertiesInfo)
        {
            var propertyName = this._storagePropertyNames[payloadPropertyInfo.Name];
            var propertyValue = payloadPropertyInfo.GetValue(dataModel);
            if (propertyValue != null)
            {
                metadata[propertyName] = ConvertToMetadataValue(propertyValue);
            }
        }

        var valuesObject = this._vectorPropertyInfo.GetValue(dataModel);
        if (valuesObject is not ReadOnlyMemory<float> values)
        {
            throw new VectorStoreRecordMappingException($"Vector property {this._vectorPropertyInfo.Name} on provided record of type {typeof(TRecord).FullName} may not be null.");
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
        var keyPropertyName = this._storagePropertyNames[this._keyPropertyInfo.Name];

        var outputJsonObject = new JsonObject
        {
            { this._keyPropertyInfo.Name, JsonValue.Create(storageModel.Id) },
        };

        if (options?.IncludeVectors is true)
        {
            var propertyName = this._storagePropertyNames[this._vectorPropertyInfo.Name];
            outputJsonObject.Add(this._vectorPropertyInfo.Name, new JsonArray(storageModel.Values.Select(x => JsonValue.Create(x)).ToArray()));
        }

        if (storageModel.Metadata != null)
        {
            foreach (var payloadProperty in this._payloadPropertiesInfo)
            {
                var propertyName = this._storagePropertyNames[payloadProperty.Name];
                if (storageModel.Metadata.TryGetValue(propertyName, out var value))
                {
                    outputJsonObject.Add(payloadProperty.Name, ConvertFromMetadataValueToJsonNode(value));
                }
            }
        }

        return outputJsonObject.Deserialize<TRecord>()!;
    }

    private static JsonNode? ConvertFromMetadataValueToJsonNode(MetadataValue metadataValue)
        => metadataValue.Inner switch
        {
            null => null,
            bool boolValue => JsonValue.Create(boolValue),
            string stringValue => JsonValue.Create(stringValue),
            int intValue => JsonValue.Create(intValue),
            long longValue => JsonValue.Create(longValue),
            float floatValue => JsonValue.Create(floatValue),
            double doubleValue => JsonValue.Create(doubleValue),
            decimal decimalValue => JsonValue.Create(decimalValue),
            MetadataValue[] array => new JsonArray(array.Select(ConvertFromMetadataValueToJsonNode).ToArray()),
            _ => throw new VectorStoreRecordMappingException($"Unsupported metadata type: '{metadataValue.Inner?.GetType().FullName}'."),
        };

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
            _ => throw new VectorStoreRecordMappingException($"Unsupported source value type '{sourceValue?.GetType().FullName}'.")
        };
}

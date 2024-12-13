// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

internal sealed class PostgresGenericDataModelMapper<TKey> : IVectorStoreRecordMapper<VectorStoreGenericDataModel<TKey>, Dictionary<string, object?>>
    where TKey : notnull
{
    /// <summary><see cref="VectorStoreRecordPropertyReader"/> with helpers for reading vector store model properties and their attributes.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresGenericDataModelMapper{TKey}"/> class.
    /// /// </summary>
    /// <param name="propertyReader"><see cref="VectorStoreRecordPropertyReader"/> with helpers for reading vector store model properties and their attributes.</param>
    public PostgresGenericDataModelMapper(VectorStoreRecordPropertyReader propertyReader)
    {
        Verify.NotNull(propertyReader);

        this._propertyReader = propertyReader;

        // Validate property types.
        this._propertyReader.VerifyDataProperties(PostgresConstants.SupportedDataTypes, PostgresConstants.SupportedEnumerableDataElementTypes);
        this._propertyReader.VerifyVectorProperties(PostgresConstants.SupportedVectorTypes);
    }

    public Dictionary<string, object?> MapFromDataToStorageModel(VectorStoreGenericDataModel<TKey> dataModel)
    {
        var properties = new Dictionary<string, object?>
        {
            // Add key property
            { this._propertyReader.KeyPropertyStoragePropertyName, dataModel.Key }
        };

        // Add data properties
        if (dataModel.Data is not null)
        {
            foreach (var property in this._propertyReader.DataProperties)
            {
                if (dataModel.Data.TryGetValue(property.DataModelPropertyName, out var dataValue))
                {
                    properties.Add(this._propertyReader.GetStoragePropertyName(property.DataModelPropertyName), dataValue);
                }
            }
        }

        // Add vector properties
        if (dataModel.Vectors is not null)
        {
            foreach (var property in this._propertyReader.VectorProperties)
            {
                if (dataModel.Vectors.TryGetValue(property.DataModelPropertyName, out var vectorValue))
                {
                    var result = PostgresVectorStoreRecordPropertyMapping.MapVectorForStorageModel(vectorValue);
                    properties.Add(this._propertyReader.GetStoragePropertyName(property.DataModelPropertyName), result);
                }
            }
        }

        return properties;
    }

    public VectorStoreGenericDataModel<TKey> MapFromStorageToDataModel(Dictionary<string, object?> storageModel, StorageToDataModelMapperOptions options)
    {
        TKey key;
        var dataProperties = new Dictionary<string, object?>();
        var vectorProperties = new Dictionary<string, object?>();

        // Process key property.
        if (storageModel.TryGetValue(this._propertyReader.KeyPropertyStoragePropertyName, out var keyObject) && keyObject is not null)
        {
            key = (TKey)keyObject;
        }
        else
        {
            throw new VectorStoreRecordMappingException("No key property was found in the record retrieved from storage.");
        }

        // Process data properties.
        foreach (var property in this._propertyReader.DataProperties)
        {
            if (storageModel.TryGetValue(this._propertyReader.GetStoragePropertyName(property.DataModelPropertyName), out var dataValue))
            {
                dataProperties.Add(property.DataModelPropertyName, dataValue);
            }
        }

        // Process vector properties
        if (options.IncludeVectors)
        {
            foreach (var property in this._propertyReader.VectorProperties)
            {
                if (storageModel.TryGetValue(this._propertyReader.GetStoragePropertyName(property.DataModelPropertyName), out var vectorValue))
                {
                    vectorProperties.Add(property.DataModelPropertyName, PostgresVectorStoreRecordPropertyMapping.MapVectorForDataModel(vectorValue));
                }
            }
        }

        return new VectorStoreGenericDataModel<TKey>(key) { Data = dataProperties, Vectors = vectorProperties };
    }
}

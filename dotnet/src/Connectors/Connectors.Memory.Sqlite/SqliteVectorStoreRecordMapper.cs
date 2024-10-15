// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Sqlite;

/// <summary>
/// Class for mapping between a dictionary and the consumer data model.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class SqliteVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>>
{
    /// <summary><see cref="VectorStoreRecordPropertyReader"/> with helpers for reading vector store model properties and their attributes.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>
    /// Initializes a new instance of the <see cref="SqliteVectorStoreRecordMapper{TRecord}"/> class.
    /// </summary>
    /// <param name="propertyReader">A <see cref="VectorStoreRecordDefinition"/> that defines the schema of the data in the database.</param>
    public SqliteVectorStoreRecordMapper(VectorStoreRecordPropertyReader propertyReader)
    {
        Verify.NotNull(propertyReader);

        this._propertyReader = propertyReader;

        this._propertyReader.VerifyHasParameterlessConstructor();

        // Validate property types.
        this._propertyReader.VerifyDataProperties(SqliteConstants.SupportedDataTypes, supportEnumerable: false);
        this._propertyReader.VerifyVectorProperties(SqliteConstants.SupportedVectorTypes);
    }

    public Dictionary<string, object?> MapFromDataToStorageModel(TRecord dataModel)
    {
        var properties = new Dictionary<string, object?>
        {
            // Add key property
            { this._propertyReader.KeyPropertyStoragePropertyName, this._propertyReader.KeyPropertyInfo.GetValue(dataModel) }
        };

        // Add data properties
        foreach (var property in this._propertyReader.DataPropertiesInfo)
        {
            properties.Add(this._propertyReader.GetStoragePropertyName(property.Name), property.GetValue(dataModel));
        }

        // Add vector properties
        foreach (var property in this._propertyReader.VectorPropertiesInfo)
        {
            object? result = null;
            var propertyValue = property.GetValue(dataModel);

            if (propertyValue is not null)
            {
                var vector = (ReadOnlyMemory<float>)propertyValue;
                result = SqliteVectorStoreRecordPropertyMapping.MapVectorForStorageModel(vector);
            }

            properties.Add(this._propertyReader.GetStoragePropertyName(property.Name), result);
        }

        return properties;
    }

    public TRecord MapFromStorageToDataModel(Dictionary<string, object?> storageModel, StorageToDataModelMapperOptions options)
    {
        var record = (TRecord)this._propertyReader.ParameterLessConstructorInfo.Invoke(null);

        // Set key.
        var keyPropertyValue = Convert.ChangeType(
            storageModel[this._propertyReader.KeyPropertyStoragePropertyName],
            this._propertyReader.KeyProperty.PropertyType);

        this._propertyReader.KeyPropertyInfo.SetValue(record, keyPropertyValue);

        // Process data properties.
        var dataPropertiesInfoWithValues = VectorStoreRecordMapping.BuildPropertiesInfoWithValues(
            this._propertyReader.DataPropertiesInfo,
            this._propertyReader.StoragePropertyNamesMap,
            storageModel);

        VectorStoreRecordMapping.SetPropertiesOnRecord(record, dataPropertiesInfoWithValues);

        if (options.IncludeVectors)
        {
            // Process vector properties.
            var vectorPropertiesInfoWithValues = VectorStoreRecordMapping.BuildPropertiesInfoWithValues(
                this._propertyReader.VectorPropertiesInfo,
                this._propertyReader.StoragePropertyNamesMap,
                storageModel,
                (object? vector, Type type) => vector is byte[] vectorBytes ?
                    SqliteVectorStoreRecordPropertyMapping.MapVectorForDataModel(vectorBytes) : null);

            VectorStoreRecordMapping.SetPropertiesOnRecord(record, vectorPropertiesInfoWithValues);
        }

        return record;
    }
}

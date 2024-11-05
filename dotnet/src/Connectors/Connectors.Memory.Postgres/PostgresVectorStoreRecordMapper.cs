// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.Postgres;

/// <summary>
/// A mapper class that handles the conversion between data models and storage models for Postgres vector store.
/// </summary>
/// <typeparam name="TRecord">The type of the data model record.</typeparam>
internal sealed class PostgresVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, Dictionary<string, object?>>
{
    /// <summary><see cref="VectorStoreRecordPropertyReader"/> with helpers for reading vector store model properties and their attributes.</summary>
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>
    /// Initializes a new instance of the <see cref="PostgresVectorStoreRecordMapper{TRecord}"/> class.
    /// </summary>
    /// <param name="propertyReader">A <see cref="VectorStoreRecordDefinition"/> that defines the schema of the data in the database.</param>
    public PostgresVectorStoreRecordMapper(VectorStoreRecordPropertyReader propertyReader)
    {
        Verify.NotNull(propertyReader);

        this._propertyReader = propertyReader;

        this._propertyReader.VerifyHasParameterlessConstructor();

        // Validate property types.
        this._propertyReader.VerifyDataProperties(PostgresConstants.SupportedDataTypes, PostgresConstants.SupportedEnumerableDataElementTypes);
        this._propertyReader.VerifyVectorProperties(PostgresConstants.SupportedVectorTypes);
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
            properties.Add(
                this._propertyReader.GetStoragePropertyName(property.Name),
                property.GetValue(dataModel)
            );
        }

        // Add vector properties
        foreach (var property in this._propertyReader.VectorPropertiesInfo)
        {
            var propertyValue = property.GetValue(dataModel);
            var result = PostgresVectorStoreRecordPropertyMapping.MapVectorForStorageModel(propertyValue);

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
                (object? vector, Type type) =>
                {
                    return PostgresVectorStoreRecordPropertyMapping.MapVectorForDataModel(vector);
                });

            VectorStoreRecordMapping.SetPropertiesOnRecord(record, vectorPropertiesInfoWithValues);
        }

        return record;
    }
}

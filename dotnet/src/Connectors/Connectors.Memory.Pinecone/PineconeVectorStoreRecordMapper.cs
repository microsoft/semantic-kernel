// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Mapper between a Pinecone record and the consumer data model that uses json as an intermediary to allow supporting a wide range of models.
/// </summary>
/// <typeparam name="TRecord">The consumer data model to map to or from.</typeparam>
internal sealed class PineconeVectorStoreRecordMapper<TRecord> : IVectorStoreRecordMapper<TRecord, Vector>
{
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
        propertyReader.VerifyKeyProperties(PineconeVectorStoreRecordFieldMapping.s_supportedKeyTypes);
        propertyReader.VerifyDataProperties(PineconeVectorStoreRecordFieldMapping.s_supportedDataTypes, PineconeVectorStoreRecordFieldMapping.s_supportedEnumerableDataElementTypes);
        propertyReader.VerifyVectorProperties(PineconeVectorStoreRecordFieldMapping.s_supportedVectorTypes);

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

        var metadata = new Metadata();
        foreach (var dataPropertyInfo in this._propertyReader.DataPropertiesInfo)
        {
            var propertyName = this._propertyReader.GetStoragePropertyName(dataPropertyInfo.Name);
            var propertyValue = dataPropertyInfo.GetValue(dataModel);
            if (propertyValue != null)
            {
                metadata[propertyName] = PineconeVectorStoreRecordFieldMapping.ConvertToMetadataValue(propertyValue);
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
            Values = values,
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
                storageModel.Values);
        }

        // Set Data.
        if (storageModel.Metadata != null)
        {
            VectorStoreRecordMapping.SetValuesOnProperties(
                outputRecord,
                this._propertyReader.DataPropertiesInfo,
                this._propertyReader.StoragePropertyNamesMap,
                storageModel.Metadata,
                PineconeVectorStoreRecordFieldMapping.ConvertFromMetadataValueToNativeType!);
        }

        return outputRecord;
    }
}

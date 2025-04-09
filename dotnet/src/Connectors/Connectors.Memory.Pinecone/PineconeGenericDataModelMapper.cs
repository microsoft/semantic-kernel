// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Pinecone;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// A mapper that maps between the generic Semantic Kernel data model and the model that the data is stored under, within Pinecone.
/// </summary>
internal sealed class PineconeGenericDataModelMapper : IVectorStoreRecordMapper<VectorStoreGenericDataModel<string>, Vector>
{
    private readonly VectorStoreRecordPropertyReader _propertyReader;

    /// <summary>
    /// Initializes a new instance of the <see cref="PineconeGenericDataModelMapper"/> class.
    /// </summary>
    /// <param name="propertyReader">A helper to access property information for the current data model and record definition.</param>
    public PineconeGenericDataModelMapper(
        VectorStoreRecordPropertyReader propertyReader)
    {
        Verify.NotNull(propertyReader);

        // Validate property types.
        propertyReader.VerifyKeyProperties(PineconeVectorStoreRecordFieldMapping.s_supportedKeyTypes);
        propertyReader.VerifyDataProperties(PineconeVectorStoreRecordFieldMapping.s_supportedDataTypes, PineconeVectorStoreRecordFieldMapping.s_supportedEnumerableDataElementTypes);
        propertyReader.VerifyVectorProperties(PineconeVectorStoreRecordFieldMapping.s_supportedVectorTypes);

        // Assign.
        this._propertyReader = propertyReader;
    }

    /// <inheritdoc />
    public Vector MapFromDataToStorageModel(VectorStoreGenericDataModel<string> dataModel)
    {
        var metadata = new Metadata();

        // Map data properties.
        foreach (var dataProperty in this._propertyReader.DataProperties)
        {
            if (dataModel.Data.TryGetValue(dataProperty.DataModelPropertyName, out var propertyValue))
            {
                var propertyStorageName = this._propertyReader.GetStoragePropertyName(dataProperty.DataModelPropertyName);
                metadata[propertyStorageName] = propertyValue is not null
                    ? PineconeVectorStoreRecordFieldMapping.ConvertToMetadataValue(propertyValue)
                    : null;
            }
        }

        // Map vector property.
        if (dataModel.Vectors.Count != 1)
        {
            throw new VectorStoreRecordMappingException($"Exactly one vector is supported by the Pinecone connector, but the provided data model contains {dataModel.Vectors.Count}.");
        }

        if (!dataModel.Vectors.TryGetValue(this._propertyReader.FirstVectorPropertyName!, out var valuesObject) || valuesObject is not ReadOnlyMemory<float> values)
        {
            throw new VectorStoreRecordMappingException($"Vector property '{this._propertyReader.FirstVectorPropertyName}' on provided record of type {nameof(VectorStoreGenericDataModel<string>)} must be of type ReadOnlyMemory<float> and not null.");
        }

        // TODO: what about sparse values?
        var result = new Vector
        {
            Id = dataModel.Key,
            Values = values,
            Metadata = metadata,
            SparseValues = null
        };

        return result;
    }

    /// <inheritdoc />
    public VectorStoreGenericDataModel<string> MapFromStorageToDataModel(Vector storageModel, StorageToDataModelMapperOptions options)
    {
        // Construct the data model.
        var dataModel = new VectorStoreGenericDataModel<string>(storageModel.Id);

        // Set Vector.
        if (options?.IncludeVectors is true)
        {
            dataModel.Vectors.Add(this._propertyReader.FirstVectorPropertyName!, storageModel.Values);
        }

        // Set Data.
        if (storageModel.Metadata != null)
        {
            foreach (var dataProperty in this._propertyReader.DataProperties)
            {
                var propertyStorageName = this._propertyReader.GetStoragePropertyName(dataProperty.DataModelPropertyName);
                if (storageModel.Metadata.TryGetValue(propertyStorageName, out var propertyValue))
                {
                    dataModel.Data[dataProperty.DataModelPropertyName] =
                        propertyValue is not null
                        ? PineconeVectorStoreRecordFieldMapping.ConvertFromMetadataValueToNativeType(propertyValue, dataProperty.PropertyType)
                        : null;
                }
            }
        }

        return dataModel;
    }
}

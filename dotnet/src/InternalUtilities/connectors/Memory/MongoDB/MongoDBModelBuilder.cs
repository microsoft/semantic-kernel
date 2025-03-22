// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Reflection;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using MongoDB.Bson.Serialization.Attributes;

namespace Microsoft.SemanticKernel.Connectors.MongoDB;

/// <summary>
/// Customized MongoDB model builder that adds specialized configuration of property storage names
/// (Mongo's reserve key property name and [BsonElement]).
/// </summary>
internal class MongoDBModelBuilder() : VectorStoreRecordModelBuilder(s_validationOptions)
{
    private static readonly VectorStoreRecordModelBuildingOptions s_validationOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,
        UsesExternalSerializer = true,

        SupportedKeyPropertyTypes = MongoDBConstants.SupportedKeyTypes,
        SupportedDataPropertyTypes = MongoDBConstants.SupportedDataTypes,
        SupportedEnumerableDataPropertyTypes = MongoDBConstants.SupportedDataTypes,
        SupportedVectorPropertyTypes = MongoDBConstants.SupportedVectorTypes
    };

    protected override void ProcessClrTypeProperties(Type clrType, VectorStoreRecordDefinition? vectorStoreRecordDefinition)
    {
        base.ProcessClrTypeProperties(clrType, vectorStoreRecordDefinition);

        foreach (var property in this.Properties)
        {
            if (property.ClrProperty?.GetCustomAttribute<BsonElementAttribute>() is { } bsonElementAttribute)
            {
                property.StorageName = bsonElementAttribute.ElementName;
            }
        }
    }

    protected override void Customize()
    {
        // Use Mongo reserved key property name as storage key property name
        if (this.KeyProperties is [var singleKeyProperty])
        {
            singleKeyProperty.StorageName = MongoDBConstants.MongoReservedKeyPropertyName;
        }
    }
}

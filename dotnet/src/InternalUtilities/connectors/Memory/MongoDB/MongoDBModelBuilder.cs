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
        SupportedEnumerableDataPropertyElementTypes = MongoDBConstants.SupportedDataTypes,
        SupportedVectorPropertyTypes = MongoDBConstants.SupportedVectorTypes
    };

    protected override void ProcessTypeProperties(Type type, VectorStoreRecordDefinition? vectorStoreRecordDefinition)
    {
        base.ProcessTypeProperties(type, vectorStoreRecordDefinition);

        foreach (var property in this.Properties)
        {
            if (property.PropertyInfo?.GetCustomAttribute<BsonElementAttribute>() is { } bsonElementAttribute)
            {
                property.StorageName = bsonElementAttribute.ElementName;
            }
        }
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

internal class AzureAISearchDynamicModelBuilder() : VectorStoreRecordModelBuilder(s_modelBuildingOptions)
{
    internal static readonly VectorStoreRecordModelBuildingOptions s_modelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,

        SupportedKeyPropertyTypes = AzureAISearchConstants.SupportedKeyTypes,
        SupportedDataPropertyTypes = AzureAISearchConstants.SupportedDataTypes,
        SupportedEnumerableDataPropertyElementTypes = AzureAISearchConstants.SupportedDataTypes,
        SupportedVectorPropertyTypes = AzureAISearchConstants.SupportedVectorTypes,

        UsesExternalSerializer = true
    };

    protected override void Validate(Type type)
    {
        base.Validate(type);

        if (this.VectorProperties.FirstOrDefault(p => p.EmbeddingGenerator is not null) is VectorStoreRecordPropertyModel property)
        {
            throw new NotSupportedException(
                $"The Azure AI Search connector does not currently support a custom embedding generator (configured for property '{property.ModelName}' on type '{type.Name}'). " +
                "However, you can configure embedding generation in Azure AI Search itself, without requiring a .NET IEmbeddingGenerator.");
        }
    }
}

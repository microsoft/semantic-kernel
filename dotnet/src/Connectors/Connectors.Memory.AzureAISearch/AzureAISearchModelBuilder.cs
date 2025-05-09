// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

internal class AzureAISearchModelBuilder() : CollectionJsonModelBuilder(s_modelBuildingOptions)
{
    internal static readonly CollectionModelBuildingOptions s_modelBuildingOptions = new()
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
}

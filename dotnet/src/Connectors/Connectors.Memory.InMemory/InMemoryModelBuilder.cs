// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData.ProviderServices;

namespace Microsoft.SemanticKernel.Connectors.InMemory;

internal class InMemoryModelBuilder() : CollectionModelBuilder(ValidationOptions)
{
    internal static readonly CollectionModelBuildingOptions ValidationOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,

        // Disable property type validation
        SupportedKeyPropertyTypes = null,
        SupportedDataPropertyTypes = null,
        SupportedEnumerableDataPropertyElementTypes = null,
        SupportedVectorPropertyTypes = [typeof(ReadOnlyMemory<float>), typeof(ReadOnlyMemory<float>?)]
    };
}

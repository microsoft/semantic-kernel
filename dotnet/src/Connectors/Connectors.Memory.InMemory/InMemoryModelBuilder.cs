// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.InMemory;

internal class InMemoryModelBuilder() : VectorStoreRecordModelBuilder(ValidationOptions)
{
    internal static readonly VectorStoreRecordModelBuildingOptions ValidationOptions = new()
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

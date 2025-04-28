// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

internal class AzureCosmosDBNoSQLVectorStoreModelBuilder() : VectorStoreRecordJsonModelBuilder(s_modelBuildingOptions)
{
    private static readonly HashSet<Type> s_supportedDataTypes =
    [
        typeof(bool),
        typeof(string),
        typeof(int),
        typeof(long),
        typeof(float),
        typeof(double),
        typeof(DateTimeOffset)
    ];

    internal static readonly HashSet<Type> s_supportedVectorTypes =
    [
        // Float32
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?),

        // Uint8
        typeof(ReadOnlyMemory<byte>),
        typeof(ReadOnlyMemory<byte>?),

        // Int8
        typeof(ReadOnlyMemory<sbyte>),
        typeof(ReadOnlyMemory<sbyte>?),
    ];

    private static readonly VectorStoreRecordModelBuildingOptions s_modelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,
        UsesExternalSerializer = true,

        // TODO: Cosmos supports other key types (int, Guid...)
        SupportedKeyPropertyTypes = [typeof(string)],
        SupportedDataPropertyTypes = s_supportedDataTypes,
        SupportedEnumerableDataPropertyElementTypes = s_supportedDataTypes,
        SupportedVectorPropertyTypes = s_supportedVectorTypes,

        ReservedKeyStorageName = AzureCosmosDBNoSQLConstants.ReservedKeyPropertyName,
    };
}

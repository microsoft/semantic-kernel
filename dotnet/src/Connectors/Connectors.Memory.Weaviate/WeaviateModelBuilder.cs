// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal class WeaviateModelBuilder() : VectorStoreRecordJsonModelBuilder(s_modelBuildingOptions)
{
    private static readonly VectorStoreRecordModelBuildingOptions s_modelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,

        SupportedKeyPropertyTypes = [typeof(Guid)],
        SupportedDataPropertyTypes = s_supportedDataTypes,
        SupportedEnumerableDataPropertyElementTypes = s_supportedDataTypes,
        SupportedVectorPropertyTypes = s_supportedVectorTypes,

        UsesExternalSerializer = true,
        ReservedKeyStorageName = WeaviateConstants.ReservedKeyPropertyName
    };

    private static readonly HashSet<Type> s_supportedDataTypes =
    [
        typeof(string),
        typeof(bool),
        typeof(int),
        typeof(long),
        typeof(short),
        typeof(byte),
        typeof(float),
        typeof(double),
        typeof(decimal),
        typeof(DateTime),
        typeof(DateTimeOffset),
        typeof(Guid),
    ];

    internal static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?),
        typeof(ReadOnlyMemory<double>),
        typeof(ReadOnlyMemory<double>?)
    ];
}

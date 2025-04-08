// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal class WeaviateModelBuilder(bool useSingleVector) : VectorStoreRecordJsonModelBuilder(GetModelBuildingOptions(useSingleVector))
{
    private static VectorStoreRecordModelBuildingOptions GetModelBuildingOptions(bool useSingleVector)
    {
        return new()
        {
            RequiresAtLeastOneVector = false,
            SupportsMultipleKeys = false,
            SupportsMultipleVectors = !useSingleVector,

            SupportedKeyPropertyTypes = [typeof(Guid)],
            SupportedDataPropertyTypes = s_supportedDataTypes,
            SupportedEnumerableDataPropertyElementTypes = s_supportedDataTypes,
            SupportedVectorPropertyTypes = s_supportedVectorTypes,

            UsesExternalSerializer = true,
            ReservedKeyStorageName = WeaviateConstants.ReservedKeyPropertyName
        };
    }

    private static readonly HashSet<Type> s_supportedDataTypes =
    [
        typeof(string),
        typeof(bool),
        typeof(bool?),
        typeof(int),
        typeof(int?),
        typeof(long),
        typeof(long?),
        typeof(short),
        typeof(short?),
        typeof(byte),
        typeof(byte?),
        typeof(float),
        typeof(float?),
        typeof(double),
        typeof(double?),
        typeof(decimal),
        typeof(decimal?),
        typeof(DateTime),
        typeof(DateTime?),
        typeof(DateTimeOffset),
        typeof(DateTimeOffset?),
        typeof(Guid),
        typeof(Guid?)
    ];

    internal static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?),
        typeof(ReadOnlyMemory<double>),
        typeof(ReadOnlyMemory<double>?)
    ];
}

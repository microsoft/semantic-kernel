// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.Extensions.VectorData.ConnectorSupport;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

internal class AzureAISearchModelBuilder() : VectorStoreRecordJsonModelBuilder(s_modelBuildingOptions)
{
    /// <summary>A set of types that a key on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedKeyTypes = [typeof(string)];

    /// <summary>A set of types that data properties on the provided model may have.</summary>
    private static readonly HashSet<Type> s_supportedDataTypes =
    [
        typeof(string),
        typeof(int),
        typeof(long),
        typeof(double),
        typeof(float),
        typeof(bool),
        typeof(DateTimeOffset)
    ];

    /// <summary>A set of types that vectors on the provided model may have.</summary>
    /// <remarks>
    /// Azure AI Search is adding support for more types than just float32, but these are not available for use via the
    /// SDK yet. We will update this list as the SDK is updated.
    /// <see href="https://learn.microsoft.com/en-us/rest/api/searchservice/supported-data-types#edm-data-types-for-vector-fields"/>
    /// </remarks>
    private static readonly HashSet<Type> s_supportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?)
    ];

    internal static readonly VectorStoreRecordModelBuildingOptions s_modelBuildingOptions = new()
    {
        RequiresAtLeastOneVector = false,
        SupportsMultipleKeys = false,
        SupportsMultipleVectors = true,

        SupportedKeyPropertyTypes = s_supportedKeyTypes,
        SupportedDataPropertyTypes = s_supportedDataTypes,
        SupportedEnumerableDataPropertyElementTypes = s_supportedDataTypes,
        SupportedVectorPropertyTypes = s_supportedVectorTypes,

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

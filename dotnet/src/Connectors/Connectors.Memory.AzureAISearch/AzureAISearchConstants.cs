// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

internal static class AzureAISearchConstants
{
    internal const string VectorStoreSystemName = "azure.aisearch";

    /// <summary>A set of types that a key on the provided model may have.</summary>
    internal static readonly HashSet<Type> SupportedKeyTypes = [typeof(string)];

    /// <summary>A set of types that data properties on the provided model may have.</summary>
    internal static readonly HashSet<Type> SupportedDataTypes =
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
    internal static readonly HashSet<Type> SupportedVectorTypes =
    [
        typeof(ReadOnlyMemory<float>),
        typeof(ReadOnlyMemory<float>?)
    ];
}

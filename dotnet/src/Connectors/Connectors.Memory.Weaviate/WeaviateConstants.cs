// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateConstants
{
    /// <summary>Reserved key property name in Weaviate.</summary>
    internal const string ReservedKeyPropertyName = "id";

    /// <summary>Reserved data property name in Weaviate.</summary>
    internal const string ReservedDataPropertyName = "properties";

    /// <summary>Reserved vector property name in Weaviate.</summary>
    internal const string ReservedVectorPropertyName = "vectors";

    /// <summary>Reserved collection property name in Weaviate.</summary>
    internal const string ReservedCollectionPropertyName = "class";
}

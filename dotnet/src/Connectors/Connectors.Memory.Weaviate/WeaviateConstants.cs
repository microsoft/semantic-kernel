// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

internal sealed class WeaviateConstants
{
    /// <summary>The name of this vector store for telemetry purposes.</summary>
    public const string VectorStoreSystemName = "weaviate";

    /// <summary>Reserved key property name in Weaviate.</summary>
    internal const string ReservedKeyPropertyName = "id";

    /// <summary>Reserved data property name in Weaviate.</summary>
    internal const string ReservedDataPropertyName = "properties";

    /// <summary>Reserved vector property name in Weaviate.</summary>
    internal const string ReservedVectorPropertyName = "vectors";

    /// <summary>Reserved single vector property name in Weaviate.</summary>
    internal const string ReservedSingleVectorPropertyName = "vector";

    /// <summary>Collection property name in Weaviate.</summary>
    internal const string CollectionPropertyName = "class";

    /// <summary>Score property name in Weaviate.</summary>
    internal const string ScorePropertyName = "distance";

    /// <summary>Score property name for hybrid search in Weaviate.</summary>
    internal const string HybridScorePropertyName = "score";

    /// <summary>Additional properties property name in Weaviate.</summary>
    internal const string AdditionalPropertiesPropertyName = "_additional";

    /// <summary>Default vectorizer for vector properties in Weaviate.</summary>
    internal const string DefaultVectorizer = "none";
}

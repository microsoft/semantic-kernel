// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Contains the list of vector search query types supported by Semantic Kernel Vector Search.
/// </summary>
[Experimental("SKEXP0001")]
public static class VectorSearchQueryType
{
    /// <summary>
    /// A type of query that searches a vector store using a vector.
    /// </summary>
    public const string VectorizedSearchQuery = nameof(VectorizedSearchQuery);

    /// <summary>
    /// A type of query that searches a vector store using a text string that will be vectorized downstream.
    /// </summary>
    public const string VectorizableTextSearchQuery = nameof(VectorizableTextSearchQuery);
}

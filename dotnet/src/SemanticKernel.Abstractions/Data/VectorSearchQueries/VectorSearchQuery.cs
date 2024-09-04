// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Contains query information to use when searching a vector store.
/// </summary>
[Experimental("SKEXP0001")]
public abstract class VectorSearchQuery
{
    /// <summary>
    /// Initializes a new instance of the <see cref="VectorSearchQuery"/> class.
    /// </summary>
    /// <param name="queryType">A string that idenifies the type of query.</param>
    /// <param name="searchOptions">The options that control the behavior of the search.</param>
    internal VectorSearchQuery(string queryType, object? searchOptions)
    {
        this.QueryType = queryType;
        this.SearchOptions = searchOptions;
    }

    /// <summary>
    /// Gets a string that identifies the type of query.
    /// </summary>
    /// <remarks>
    /// For a list of types see <see cref="VectorSearchQueryType"/>.
    /// </remarks>
    public string QueryType { get; }

    /// <summary>
    /// Gets the options that control the behavior of the search.
    /// </summary>
    public object? SearchOptions { get; }

    /// <summary>
    /// Creates a new query to search a vector store using a vector.
    /// </summary>
    /// <typeparam name="TVector">The type of the vector.</typeparam>
    /// <param name="vector">The vector to search the store with.</param>
    /// <param name="options">The options that control the behavior of the search.</param>
    /// <returns>The query object.</returns>
    public static VectorizedSearchQuery<TVector> CreateQuery<TVector>(TVector vector, VectorSearchOptions? options = default) => new(vector, options);

    /// <summary>
    /// Creates a new query to search a vector store using a text string that will be vectorized downstream.
    /// </summary>
    /// <param name="searchText">The text to search the store with.</param>
    /// <param name="options">The options that control the behavior of the search.</param>
    /// <returns>The query object.</returns>
    public static VectorizableTextSearchQuery CreateQuery(string searchText, VectorSearchOptions? options = default) => new(searchText, options);
}

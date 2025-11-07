// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Represents a filter clause that adds terms to the search query itself for text search engines.
/// </summary>
/// <remarks>
/// This filter clause is used when the underlying search service should add the specified
/// terms to the search query to help find matching results, rather than filtering results
/// after they are returned.
///
/// Primary use case: Supporting Title.Contains("value") LINQ expressions for search engines
/// that don't have field-specific operators (e.g., Brave, Tavily). The implementation extracts
/// the search term and appends it to the base query for enhanced relevance.
///
/// Example: Title.Contains("AI") → SearchQueryFilterClause("AI") → query + " AI"
///
/// See ADR-TextSearch-Contains-Support.md for architectural context and cross-engine comparison.
/// </remarks>
public sealed class SearchQueryFilterClause : FilterClause
{
    /// <summary>
    /// Initializes a new instance of the <see cref="SearchQueryFilterClause"/> class.
    /// </summary>
    /// <param name="searchTerm">The term to add to the search query.</param>
    public SearchQueryFilterClause(string searchTerm)
    {
        this.SearchTerm = searchTerm;
    }

    /// <summary>
    /// Gets the search term to add to the query.
    /// </summary>
    public string SearchTerm { get; private set; }
}

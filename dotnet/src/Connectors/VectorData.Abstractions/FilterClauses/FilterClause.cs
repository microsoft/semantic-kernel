// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Base class for filter clauses.
/// </summary>
/// <remarks>
/// A <see cref="FilterClause"/> is used to request that the underlying search service should
/// filter search results based on the specified criteria.
/// </remarks>
public abstract class FilterClause
{
    internal FilterClause()
    {
    }
}

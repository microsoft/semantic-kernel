// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.Extensions.VectorData;

/// <summary>
/// Defines a base class for filter clauses.
/// </summary>
/// <remarks>
/// A <see cref="FilterClause"/> is used to request that the underlying search service should
/// filter search results based on the specified criteria.
/// </remarks>
[Obsolete("Use LINQ expressions via TextSearchOptions<TRecord>.Filter instead. This type will be removed in a future version.")]
public abstract class FilterClause
{
    /// <summary>
    /// Initializes a new instance of the <see cref="FilterClause"/> class.
    /// </summary>
    protected FilterClause()
    {
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Base class for filter clauses.
/// </summary>
/// <remarks>
/// A <see cref="FilterClause"/> is used to request that the underlying search service should
/// filter search results based on the specified criteria.
/// </remarks>
[Experimental("SKEXP0001")]
public abstract class FilterClause
{
}

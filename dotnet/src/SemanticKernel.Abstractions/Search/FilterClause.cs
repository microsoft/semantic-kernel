// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Base class for filter clauses.
/// </summary>
/// <remarks>
/// The <see cref="FilterClause"/> is used to request that the underlying search service should
/// filter search results based on the specified criteria.
/// </remarks>
[Experimental("SKEXP0001")]
public abstract class FilterClause;

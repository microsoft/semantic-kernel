// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Search;

/// <summary>
/// Delegate to map a search result instance from an arbitrary <see cref="object"/> to a <see cref="string"/>
/// </summary>
/// <param name="result">The search result to be mapped.</param>
public delegate string MapSearchResultToString(object result);

/// <summary>
/// Delegate to map a search result instance from an arbitrary <see cref="object"/> to a <see cref="TextSearchResult"/>
/// </summary>
/// <param name="result">The search result to be mapped.</param>
public delegate TextSearchResult MapSearchResultToTextSearchResult(object result);

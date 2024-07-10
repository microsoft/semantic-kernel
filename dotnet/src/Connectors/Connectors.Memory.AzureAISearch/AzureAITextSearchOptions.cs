// Copyright (c) Microsoft. All rights reserved.

using Azure.Search.Documents.Models;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// Options used to construct an instance of <see cref="AzureAITextSearch"/>
/// </summary>
public sealed class AzureAITextSearchOptions
{
    /// <summary>
    ///  Delegate to map a <see cref="SearchDocument"/> instance to a <see cref="string"/>
    /// </summary>
    public MapSearchDocumentToString? MapToString { get; init; } = null;

    /// <summary>
    /// Delegate to map a <see cref="SearchDocument"/> instance to a <see cref="TextSearchResult"/>
    /// </summary>
    public MapSearchDocumentToTextSearchResult? MapToTextSearchResult { get; init; } = null;
}

/// <summary>
/// Delegate to map a <see cref="SearchDocument"/> instance to a <see cref="string"/>
/// </summary>
public delegate string MapSearchDocumentToString(SearchDocument document);

/// <summary>
/// Delegate to map a <see cref="SearchDocument"/> instance to a <see cref="TextSearchResult"/>
/// </summary>
public delegate TextSearchResult MapSearchDocumentToTextSearchResult(SearchDocument document);

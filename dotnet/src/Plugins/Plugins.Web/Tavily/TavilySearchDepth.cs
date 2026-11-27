// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Plugins.Web.Tavily;

/// <summary>
/// The depth of the search. advanced search is tailored to retrieve
/// the most relevant sources and content snippets for your query,
/// while basic search provides generic content snippets from each source.
/// </summary>
public enum TavilySearchDepth
{
    /// <summary>
    /// Basic search costs 1 API Credit.
    /// </summary>
    Basic,
    /// <summary>
    /// Advanced search costs 2 API Credits.
    /// </summary>
    Advanced,

    /// <summary>
    /// Fast search prioritizes lower latency while maintaining good relevance. Costs 1 API Credit.
    /// </summary>
    Fast,

    /// <summary>
    /// Ultra-fast search minimizes latency above all else. Costs 1 API Credit.
    /// </summary>
    UltraFast
}

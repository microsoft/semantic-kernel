// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Plugins.Web.Tavily;

/// <summary>
/// Controls how the include domain filter is applied to a Tavily search.
/// </summary>
public enum TavilyIncludeDomainsMode
{
    /// <summary>
    /// Limit results to only the included domains (Tavily default).
    /// </summary>
    Restrict,

    /// <summary>
    /// Also search the rest of the web, so results outside the included domains can still surface.
    /// </summary>
    Prefer
}

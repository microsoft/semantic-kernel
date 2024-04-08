// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Services;

/// <summary>
/// Represents a search service.
/// </summary>
public interface ISearchService
{
    /// <summary>
    /// Gets the search service attributes.
    /// </summary>
    IReadOnlyDictionary<string, object?> Attributes { get; }
}

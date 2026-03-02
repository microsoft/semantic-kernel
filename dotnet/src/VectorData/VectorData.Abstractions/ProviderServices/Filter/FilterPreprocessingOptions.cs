// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.Extensions.VectorData.ProviderServices.Filter;

/// <summary>
/// Options for filter expression preprocessing.
/// This is an internal support type meant for use by connectors only and not by applications.
/// </summary>
[Experimental("MEVD9001")]
public class FilterPreprocessingOptions
{
    /// <summary>
    /// Whether the connector supports parameterization.
    /// </summary>
    /// <remarks>
    /// If <see langword="false"/>, the visitor will inline captured variables and constant member accesses as simple constant nodes.
    /// If <see langword="true"/>, these will instead be replaced with <see cref="QueryParameterExpression"/> nodes.
    /// </remarks>
    public bool SupportsParameterization { get; init; }
}

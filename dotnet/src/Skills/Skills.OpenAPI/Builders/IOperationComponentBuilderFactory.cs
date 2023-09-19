// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Skills.OpenAPI.Builders.Query;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Builders;

/// <summary>
/// Defines an interface for creating builders used to construct various components(path, query string, payload, etc...) of REST API operations.
/// </summary>
internal interface IOperationComponentBuilderFactory
{
    /// <summary>
    /// Creates a new instance of <see cref="IQueryStringBuilder"/> for building query strings.
    /// </summary>
    /// <returns>An instance of <see cref="IQueryStringBuilder"/>.</returns>
    IQueryStringBuilder CreateQueryStringBuilder();
}

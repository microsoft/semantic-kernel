// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Skills.OpenAPI.Builders.Query;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Builders;

/// <summary>
/// Defines factory for creating builders used to construct various components(path, query string, payload, etc...) of REST API operations.
/// </summary>
internal class OperationComponentBuilderFactory : IOperationComponentBuilderFactory
{
    private readonly Lazy<IQueryStringBuilder> queryStringBuilder = new(() => new QueryStringBuilder());

    /// <inheritdoc/>
    public IQueryStringBuilder CreateQueryStringBuilder()
    {
        return this.queryStringBuilder.Value;
    }
}

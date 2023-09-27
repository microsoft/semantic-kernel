// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Functions.OpenAPI.Builders.Query;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Builders;

/// <summary>
/// Defines factory for creating builders used to construct various components(path, query string, payload, etc...) of REST API operations.
/// </summary>
internal sealed class OperationComponentBuilderFactory : IOperationComponentBuilderFactory
{
    private readonly Lazy<IQueryStringBuilder> _queryStringBuilder = new(() => new QueryStringBuilder());

    /// <inheritdoc/>
    public IQueryStringBuilder CreateQueryStringBuilder()
    {
        return this._queryStringBuilder.Value;
    }
}

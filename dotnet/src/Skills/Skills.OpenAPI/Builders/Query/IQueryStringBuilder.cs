// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Builders.Query;

/// <summary>
/// Represents a query string builder interface for REST API operations.
/// </summary>
internal interface IQueryStringBuilder
{
    /// <summary>
    /// Builds a query string for the specified REST API operation.
    /// </summary>
    /// <param name="operation">The REST API operation.</param>
    /// <param name="arguments">A dictionary containing query string arguments.</param>
    /// <returns>The constructed query string.</returns>
    string Build(RestApiOperation operation, IDictionary<string, string> arguments);
}

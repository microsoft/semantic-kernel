// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.WebApi.Rest.Model;

namespace Microsoft.SemanticKernel.Connectors.WebApi.Rest;

/// <summary>
/// Interface for REST API operation runner classes.
/// </summary>
internal interface IRestApiOperationRunner
{
    /// <summary>
    /// Runs a REST API operation.
    /// </summary>
    /// <param name="operation">The operation to run.</param>
    /// <param name="arguments">The operation arguments.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The result of the operation run.</returns>
    Task<JsonNode?> RunAsync(RestApiOperation operation, IDictionary<string, string> arguments, CancellationToken cancellationToken = default);
}

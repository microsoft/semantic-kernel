// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Skills.OpenAPI.Model;

namespace Microsoft.SemanticKernel.Skills.OpenAPI.Rest;

/// <summary>
/// Interface for Rest operation runner classes.
/// </summary>
internal interface IRestOperationRunner
{
    /// <summary>
    /// Runs an Rest operation.
    /// </summary>
    /// <param name="operation">The operation to run.</param>
    /// <param name="arguments">The arguments.</param>
    /// <param name="payload">The payload</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The result of the operation run.</returns>
    Task<JsonNode?> RunAsync(RestOperation operation, IDictionary<string, string> arguments, JsonNode? payload = null, CancellationToken cancellationToken = default);
}

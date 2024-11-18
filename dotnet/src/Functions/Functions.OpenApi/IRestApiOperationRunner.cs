// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

internal interface IRestApiOperationRunner
{
    /// <summary>
    /// Executes the specified <paramref name="operation"/> asynchronously, using the provided <paramref name="arguments"/>.
    /// </summary>
    /// <param name="operation">The REST API operation to execute.</param>
    /// <param name="arguments">The dictionary of arguments to be passed to the operation.</param>
    /// <param name="options">Options for REST API operation run.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>The task execution result.</returns>
    public Task<RestApiOperationResponse> RunAsync(
        RestApiOperation operation,
        KernelArguments arguments,
        RestApiOperationRunOptions? options = null,
        CancellationToken cancellationToken = default);
}

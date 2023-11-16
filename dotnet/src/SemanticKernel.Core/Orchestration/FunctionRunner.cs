// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Function runner implementation.
/// </summary>
internal class FunctionRunner : IFunctionRunner
{
    private readonly IKernel _kernel;

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionRunner"/> class.
    /// </summary>
    /// <param name="kernel">The kernel instance.</param>
    public FunctionRunner(IKernel kernel)
    {
        this._kernel = kernel;
    }

    /// <inheritdoc/>
    public async Task<FunctionResult?> RunAsync(ISKFunction skFunction, ContextVariables? variables = null, CancellationToken cancellationToken = default)
    {
        return (await this._kernel.RunAsync(skFunction, variables, cancellationToken).ConfigureAwait(false))
            .FunctionResults.FirstOrDefault();
    }

    /// <inheritdoc/>
    public Task<FunctionResult?> RunAsync(string pluginName, string functionName, ContextVariables? variables = null, CancellationToken cancellationToken = default)
    {
        var function = this._kernel.Functions.GetFunction(pluginName, functionName);
        return this.RunAsync(function, variables, cancellationToken);
    }

    public IAsyncEnumerable<StreamingResultChunk> StreamingRunAsync(ISKFunction skFunction, ContextVariables? variables = null, CancellationToken cancellationToken = default)
    {
        return this._kernel.StreamingRunAsync(skFunction, variables, cancellationToken);
    }

    public IAsyncEnumerable<StreamingResultChunk> StreamingRunAsync(string pluginName, string functionName, ContextVariables? variables = null, CancellationToken cancellationToken = default)
    {
        throw new System.NotImplementedException();
    }
}

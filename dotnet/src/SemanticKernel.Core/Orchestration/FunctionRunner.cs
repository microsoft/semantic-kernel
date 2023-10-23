// Copyright (c) Microsoft. All rights reserved.

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
    public async Task<FunctionResult> RunAsync(
        ISKFunction skFunction,
        ContextVariables? variables = null,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        return (await this._kernel.RunAsync(variables ?? new(), requestSettings, cancellationToken, skFunction).ConfigureAwait(false))
            .FunctionResults.First();
    }

    /// <inheritdoc/>
    public Task<FunctionResult> RunAsync(string pluginName, string functionName, ContextVariables? variables = null, CancellationToken cancellationToken = default)
    {
        var function = this._kernel.Functions.GetFunction(pluginName, functionName);
        return this.RunAsync(function, variables, null, cancellationToken);
    }
}

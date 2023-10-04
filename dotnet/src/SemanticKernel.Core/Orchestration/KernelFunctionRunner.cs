// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Orchestration;
internal class KernelFunctionRunner : IFunctionRunner
{
    private readonly IKernel _kernel;
    public KernelFunctionRunner(IKernel kernel)
    {
        this._kernel = kernel;
    }

    public async Task<FunctionResult> RunAsync(ISKFunction skFunction, ContextVariables variables, CancellationToken cancellationToken = default)
    {
        return (await this._kernel.RunAsync(skFunction, variables, cancellationToken).ConfigureAwait(false))
            .FunctionResults.First();
    }

    public Task<FunctionResult> RunAsync(string pluginName, string functionName, ContextVariables variables, CancellationToken cancellationToken = default)
    {
        var function = this._kernel.Functions.GetFunction(pluginName, functionName);
        return this.RunAsync(function, variables, cancellationToken);
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Kernel function executor implementation
/// </summary>
internal sealed class FunctionExecutor : IFunctionExecutor
{
    private readonly Kernel _originKernel;

    internal FunctionExecutor(Kernel originKernel)
    {
        this._originKernel = originKernel;
    }

    /// <inheritdoc/>
    public Task<KernelResult> ExecuteAsync(ISKFunction skFunction, ContextVariables variables, IReadOnlyFunctionCollection? functions = null, CancellationToken cancellationToken = default)
    {
        using var kernel = this._originKernel.Clone(functions);
        return kernel.RunAsync(variables, cancellationToken, skFunction);
    }
}

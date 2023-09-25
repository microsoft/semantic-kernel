// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Kernel execution context implementation
/// This will live during the execution of functions.
/// </summary>
internal sealed class KernelExecutionContext : IKernelExecutionContext, IDisposable
{
    private readonly Kernel _kernel;

    /// <inheritdoc/>
    public ILoggerFactory LoggerFactory => this._kernel.LoggerFactory;

    /// <inheritdoc/>
    public IReadOnlyFunctionCollection Functions => this._kernel.Functions;

    internal KernelExecutionContext(Kernel kernel,
        IReadOnlyFunctionCollection functionCollection,
        IAIServiceProvider aiServiceProvider)
    {
        this._kernel = new Kernel(
            new FunctionCollection(functionCollection),
            aiServiceProvider,
            kernel.PromptTemplateEngine,
            kernel.Memory,
            kernel.HttpHandlerFactory,
            kernel.LoggerFactory);
    }

    /// <inheritdoc/>
    public Task<KernelResult> RunAsync(ISKFunction skFunction, ContextVariables variables, CancellationToken cancellationToken = default)
    {
        return this._kernel.RunAsync(variables, cancellationToken, skFunction);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._kernel.Dispose();
    }
}

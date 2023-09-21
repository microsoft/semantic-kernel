// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Kernel execution context implementation
/// This will live during the execution of functions.
/// </summary>
internal sealed class KernelExecutionContext : IKernelExecutionContext, IDisposable
{
    private Kernel _kernel;

    /// <inheritdoc/>
    public ILoggerFactory LoggerFactory => this._kernel.LoggerFactory;

    /// <inheritdoc/>
    public IReadOnlyFunctionCollection Functions => this._kernel.Functions;

    internal KernelExecutionContext(
        IReadOnlyFunctionCollection skillCollection,
        IAIServiceProvider aiServiceProvider,
        IPromptTemplateEngine promptTemplateEngine,
        ISemanticTextMemory memory,
        IDelegatingHandlerFactory httpHandlerFactory,
        ILoggerFactory loggerFactory)
    {
        this._kernel = new Kernel(
            new FunctionCollection(skillCollection),
            aiServiceProvider,
            promptTemplateEngine,
            memory,
            httpHandlerFactory,
            loggerFactory);
    }

    /// <inheritdoc/>
    public Task<SKContext> RunAsync(ContextVariables variables, ISKFunction[] pipeline, CancellationToken cancellationToken = default)
    {
        return this._kernel.RunAsync(variables, cancellationToken, pipeline);
    }

    /// <inheritdoc/>
    public void Dispose()
    {
        this._kernel.Dispose();
    }

    /// <inheritdoc/>
    public SKContext CreateNewContext(ContextVariables? variables = null, IReadOnlyFunctionCollection? skills = null)
        => this._kernel.CreateNewContext(variables, skills);
}

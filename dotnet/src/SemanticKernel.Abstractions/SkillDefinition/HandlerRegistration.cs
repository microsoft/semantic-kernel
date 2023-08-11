// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Request to the execution handler. Can be used to cancel the execution.
/// </summary>
/// <typeparam name="TExecutionContext"></typeparam>
public sealed class HandlerRegistration<TExecutionContext>
{
    /// <summary>
    /// Previous execution handler.
    /// </summary>
    private readonly HandlerRegistration<TExecutionContext>? _priorExecutionHandler = null;

    /// <summary>
    /// Gets a value indicating whether the request has been canceled.
    /// </summary>
    public bool IsCanceled { get; private set; } = false;

    /// <summary>
    /// Gets the execution handler delegate.
    /// </summary>
    public ExecutionHandler<TExecutionContext> ExecutionHandler { get; }

    /// <summary>
    /// Creates a new instance of the <see cref="HandlerRegistration{TExecutionContext}"/> class.
    /// </summary>
    /// <param name="executionHandler">Delegate reference</param>
    /// <param name="priorHandlerRequest">Prior delegate reference</param>
    internal HandlerRegistration(ExecutionHandler<TExecutionContext> executionHandler, HandlerRegistration<TExecutionContext>? priorHandlerRequest = null)
    {
        Verify.NotNull(executionHandler);
        this.ExecutionHandler = executionHandler;

        if (priorHandlerRequest is not null)
        {
            this._priorExecutionHandler = priorHandlerRequest;
        }
    }

    /// <summary>
    /// Invokes the execution Handler.
    /// </summary>
    /// <param name="context">Execution context abstraction</param>
    /// <returns>Task Completed</returns>
    internal async Task InvokeAsync(TExecutionContext context)
    {
        try
        {
            if (!this.IsCanceled)
            {
                await this.ExecutionHandler.Invoke(context).ConfigureAwait(false);
            }
        }
        finally
        {
            if (this._priorExecutionHandler is not null)
            {
                await this._priorExecutionHandler.InvokeAsync(context).ConfigureAwait(false);
            }
        }
    }

    /// <summary>
    /// Sets the request state to be cancelled.
    /// This will prevent any future execution of the handler.
    /// </summary>
    public void Cancel()
    {
        this.IsCanceled = true;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Request to the execution hook. Can be used to cancel the execution.
/// </summary>
/// <typeparam name="TExecutionContext"></typeparam>
public sealed class HookRequest<TExecutionContext>
{
    /// <summary>
    /// Previous execution hook.
    /// </summary>
    private readonly ExecutionHook<TExecutionContext>? _priorExecutionHook = null;

    /// <summary>
    /// Gets a value indicating whether the request has been canceled.
    /// </summary>
    public bool Canceled { get; private set; } = false;

    /// <summary>
    /// Gets the execution hook delegate.
    /// </summary>
    public ExecutionHook<TExecutionContext> ExecutionHook { get; }

    /// <summary>
    /// Creates a new instance of the <see cref="HookRequest{TExecutionContext}"/> class.
    /// </summary>
    /// <param name="executionHook">Delegate reference</param>
    /// <param name="priorHookRequest">Prior delegate reference</param>
    internal HookRequest(ExecutionHook<TExecutionContext> executionHook, HookRequest<TExecutionContext>? priorHookRequest = null)
    {
        Verify.NotNull(executionHook);
        this.ExecutionHook = executionHook;

        if (priorHookRequest is not null)
        {
            this._priorExecutionHook = priorHookRequest.ExecutionHook;
        }
    }

    /// <summary>
    /// Invokes the execution hook.
    /// </summary>
    /// <param name="context">Execution context abstraction</param>
    /// <returns>Task Completed</returns>
    internal async Task InvokeAsync(TExecutionContext context)
    {
        try
        {
            if (!this.Canceled)
            {
                await this.ExecutionHook.Invoke(context).ConfigureAwait(false);
            }
        }
        finally
        {
            if (this._priorExecutionHook is not null)
            {
                await this._priorExecutionHook.Invoke(context).ConfigureAwait(false);
            }
        }
    }

    /// <summary>
    /// Sets the request state to be cancelled.
    /// This will prevent any future execution of the hook.
    /// </summary>
    public void Cancel()
    {
        this.Canceled = true;
    }
}

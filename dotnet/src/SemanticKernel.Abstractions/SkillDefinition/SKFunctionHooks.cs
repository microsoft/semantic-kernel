// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

public delegate Task ExecutionHook<TExecutionContext>(TExecutionContext context);

public sealed class PreExecutionContext
{
    internal PreExecutionContext(SKContext context, string? prompt = null)
    {
        Verify.NotNull(context);

        this.SKContext = context;
        this.Prompt = prompt;
    }

    public SKContext SKContext { get; }
    public string? Prompt { get; }
}

public sealed class PostExecutionContext
{
    internal PostExecutionContext(SKContext context)
    {
        Verify.NotNull(context);

        this.SKContext = context;
    }

    public SKContext SKContext { get; }
}

public sealed class HookRequest<TExecutionContext>
{
    private readonly ExecutionHook<TExecutionContext>? _priorExecutionHook = null;

    public bool Canceled { get; private set; } = false;
    public ExecutionHook<TExecutionContext> ExecutionHook { get; }

    internal HookRequest(ExecutionHook<TExecutionContext> executionHook, HookRequest<TExecutionContext>? priorHookRequest = null)
    {
        Verify.NotNull(executionHook);
        this.ExecutionHook = executionHook;

        if (priorHookRequest is not null)
        {
            this._priorExecutionHook = priorHookRequest.ExecutionHook;
        }
    }

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
    /// Cancel the execution of the hook.
    /// </summary>
    public void Cancel()
    {
        this.Canceled = true;
    }
}

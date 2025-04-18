// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks.Sources;

namespace Microsoft.AgentRuntime.InProcess;

internal interface IResultSink<TResult> : IValueTaskSource<TResult>
{
    public void SetResult(TResult result);
    public void SetException(Exception exception);
    public void SetCancelled(OperationCanceledException? exception = null);

    public ValueTask<TResult> Future { get; }
}

internal sealed class ResultSink<TResult> : IResultSink<TResult>
{
    private ManualResetValueTaskSourceCore<TResult> core;

    public bool IsCancelled { get; private set; }

    public TResult GetResult(short token)
    {
        return this.core.GetResult(token);
    }

    public ValueTaskSourceStatus GetStatus(short token)
    {
        return this.core.GetStatus(token);
    }

    public void OnCompleted(Action<object?> continuation, object? state, short token, ValueTaskSourceOnCompletedFlags flags)
    {
        this.core.OnCompleted(continuation, state, token, flags);
    }

    public void SetCancelled(OperationCanceledException? exception = null)
    {
        this.IsCancelled = true;
        this.core.SetException(exception ?? new OperationCanceledException());
    }

    public void SetException(Exception exception)
    {
        this.core.SetException(exception);
    }

    public void SetResult(TResult result)
    {
        this.core.SetResult(result);
    }

    public ValueTask<TResult> Future => new(this, this.core.Version);
}

// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace VectorDataSpecificationTests.Support;

#pragma warning disable CA1001 // Type owns disposable fields but is not disposable

public abstract class TestStore
{
    private readonly SemaphoreSlim _lock = new(1, 1);
    private int _referenceCount;

    protected abstract Task StartAsync();

    protected virtual Task StopAsync()
        => Task.CompletedTask;

    public virtual async Task ReferenceCountingStartAsync()
    {
        await this._lock.WaitAsync();
        try
        {
            if (this._referenceCount++ == 0)
            {
                await this.StartAsync();
            }
        }
        finally
        {
            this._lock.Release();
        }
    }

    public virtual async Task ReferenceCountingStopAsync()
    {
        await this._lock.WaitAsync();
        try
        {
            if (--this._referenceCount == 0)
            {
                await this.StopAsync();
            }
        }
        finally
        {
            this._lock.Release();
        }
    }

    public abstract IVectorStore DefaultVectorStore { get; }
}

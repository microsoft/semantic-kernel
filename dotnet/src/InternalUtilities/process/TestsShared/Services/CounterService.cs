// Copyright (c) Microsoft. All rights reserved.

using System.Threading;

namespace Microsoft.SemanticKernel.Process.TestsShared.Services;

internal sealed class CounterService : ICounterService
{
    internal int _counter = 0;
    public int GetCount()
    {
        return this._counter;
    }

    public int IncreaseCount()
    {
        Interlocked.Increment(ref this._counter);
        return this._counter;
    }

    public void SetCount(int count)
    {
        this._counter = count;
    }
}

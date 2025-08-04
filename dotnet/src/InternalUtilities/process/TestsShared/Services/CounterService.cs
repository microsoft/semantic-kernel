// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0005 // Using directive is unnecessary
using System.Threading;
#pragma warning restore IDE0005 // Using directive is unnecessary

namespace Microsoft.SemanticKernel.Process.TestsShared.Services;

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
internal sealed class CounterService : ICounterService
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
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

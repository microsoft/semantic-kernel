// Copyright (c) Microsoft. All rights reserved.

namespace SemanticKernel.Process.TestsShared.Services;

internal sealed class CounterService : ICounterService
{
    internal int _counter = 0;
    public int GetCount()
    {
        return this._counter;
    }

    public int IncreateCount()
    {
        this._counter++;
        return this._counter;
    }
}

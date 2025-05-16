// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;
internal sealed class ProcessStateManager
{
    private readonly Type? _stateType;
    private object? _instance;

    public ProcessStateManager(Type? stateType, object? initialState = null)
    {
        this._stateType = stateType;
        this._instance = initialState;

        if (initialState is null && stateType is not null)
        {
            // Create an instance of the state type if not provided
            this._instance = Activator.CreateInstance(stateType);
        }
    }

    public async Task ReduceAsync(Func<Type, object?, Task<object?>> func)
    {
        Verify.NotNull(func);
        if (this._stateType is null)
        {
            throw new KernelException("State type is not defined.");
        }

        this._instance = await func(this._stateType, this._instance).ConfigureAwait(false);
    }

    public object? GetState()
    {
        if (this._stateType is null)
        {
            return null;
        }

        // return a deep copy of the state
        var json = JsonSerializer.Serialize(this._instance, this._stateType);
        return JsonSerializer.Deserialize(json, this._stateType);
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Process;

internal class LocalUserStateStore : IKernelProcessUserStateStore
{
    public Dictionary<string, object> UserState { get; private set; } = [];

    public void ResetUserState(Dictionary<string, object> newValues)
    {
        // Should it reset all dictionary or only update newValues keys?
        //this._userState = new Dictionary<string, object>(newValues, StringComparer.OrdinalIgnoreCase);
        foreach (var item in newValues)
        {
            this.UserState[item.Key] = item.Value;
        }
    }

    /// <summary>
    /// Gets the user state of the process.
    /// </summary>
    /// <param name="key">The key to identify the user state.</param>
    /// <typeparam name="T"></typeparam>
    /// <returns></returns>
    public Task<T> GetUserStateAsync<T>(string key) where T : class
    {
        if (this.UserState.TryGetValue(key, out var value) && value is T typedValue)
        {
            return Task.FromResult(typedValue);
        }

        return Task.FromResult<T>(null!); // HACK
    }

    /// <summary>
    /// Sets the user state of the process.
    /// </summary>
    /// <typeparam name="T"></typeparam>
    /// <param name="key"></param>
    /// <param name="state"></param>
    /// <returns></returns>
    public Task SetUserStateAsync<T>(string key, T state) where T : class
    {
        this.UserState[key] = state ?? throw new ArgumentNullException(nameof(state), "State cannot be null.");
        return Task.CompletedTask;
    }
}

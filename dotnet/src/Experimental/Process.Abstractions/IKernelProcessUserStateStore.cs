// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
///  interface for a store that manages user state for kernel processes.
/// </summary>
public interface IKernelProcessUserStateStore
{
    /// <summary>
    /// Defines the key used to store user state in the store.
    /// </summary>
    /// <typeparam name="T"></typeparam>
    /// <param name="key"></param>
    /// <returns></returns>
    Task<T> GetUserStateAsync<T>(string key) where T : class;

    /// <summary>
    /// Sets the user state in the store.
    /// </summary>
    /// <typeparam name="T"></typeparam>
    /// <param name="key"></param>
    /// <param name="state"></param>
    /// <returns></returns>
    Task SetUserStateAsync<T>(string key, T state) where T : class;
}

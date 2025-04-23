// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// A collection of all the registered <see cref="KernelProcess"/> services with associated keys
/// </summary>
/// <param name="sc">The <see cref="IServiceCollection"/></param>
public sealed class KeyedProcesses(IServiceCollection sc)
{
    /// <summary>
    /// The keys of all the registered <see cref="KernelProcess"/> services
    /// </summary>
    public IReadOnlyList<string> Keys { get; } = [..
        from service in sc
        where service.ServiceKey != null
        where service.ServiceKey!.GetType() == typeof(string)
        where service.ServiceType == typeof(KernelProcess)
        select (string)service.ServiceKey!];
}

/// <summary>
/// A dictionary of all the keys for the <see cref="KernelProcess"/> services
/// </summary>
/// <param name="keys"></param>
/// <param name="provider"></param>
public sealed class KeyedServiceDictionary(
        KeyedProcesses keys, IServiceProvider provider)
        : ReadOnlyDictionary<string, KernelProcess>(Create(keys, provider))
{
    private static Dictionary<string, KernelProcess> Create(
        KeyedProcesses keys, IServiceProvider provider)
    {
        var dict = new Dictionary<string, KernelProcess>(capacity: keys.Keys.Count);

        foreach (string key in keys.Keys)
        {
            dict[key] = provider.GetRequiredKeyedService<KernelProcess>(key);
        }

        return dict;
    }
}

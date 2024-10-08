// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Dapr.Actors;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface that represents a process.
/// </summary>
public interface IProcess : IActor
{
    Task InitializeProcessAsync(DaprProcessInfo processInfo, string? parentProcessId);

    Task StartAsync(bool keepAlive);

    Task RunOnceAsync(KernelProcessEvent processEvent);

    Task StopAsync();

    Task SendMessageAsync(KernelProcessEvent processEvent);

    Task<DaprProcessInfo> GetProcessInfoAsync();
}

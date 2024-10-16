﻿// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Dapr.Actors;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface that represents a process.
/// </summary>
public interface IProcess : IActor
{
    /// <summary>
    /// Initializes the process with the specified instance of <see cref="DaprProcessInfo"/>.
    /// </summary>
    /// <param name="processInfo">Used to initialize the process.</param>
    /// <param name="parentProcessId">The parent Id of the process if one exists.</param>
    /// <returns>A<see cref="Task"/></returns>
    Task InitializeProcessAsync(DaprProcessInfo processInfo, string? parentProcessId);

    /// <summary>
    /// Starts an initialized process.
    /// </summary>
    /// <param name="keepAlive">Indicates if the process should wait for external events after it's finished processing.</param>
    /// <returns></returns>
    Task StartAsync(bool keepAlive);

    /// <summary>
    /// Starts the process with an initial event and then waits for the process to finish. In this case the process will not
    /// keep alive waiting for external events after the internal messages have stopped.
    /// </summary>
    /// <param name="processEvent">Required. The <see cref="KernelProcessEvent"/> to start the process with.</param>
    /// <returns>A <see cref="Task"/></returns>
    Task RunOnceAsync(KernelProcessEvent processEvent);

    /// <summary>
    /// Stops a running process. This will cancel the process and wait for it to complete before returning.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    Task StopAsync();

    /// <summary>
    /// Sends a message to the process. This does not start the process if it's not already running, in
    /// this case the message will remain queued until the process is started.
    /// </summary>
    /// <param name="processEvent">Required. The <see cref="KernelProcessEvent"/> to start the process with.</param>
    /// <returns>A <see cref="Task"/></returns>
    Task SendMessageAsync(KernelProcessEvent processEvent);

    /// <summary>
    /// Gets the process information.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcess"/></returns>
    Task<DaprProcessInfo> GetProcessInfoAsync();
}

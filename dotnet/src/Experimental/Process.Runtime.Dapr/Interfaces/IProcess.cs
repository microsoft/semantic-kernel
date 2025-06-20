// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Dapr.Actors;

namespace Microsoft.SemanticKernel;

/// <summary>
/// An interface that represents a process.
/// </summary>
public interface IProcess : IActor, IStep
{
    /// <summary>
    /// Initializes the process with the specified instance of <see cref="DaprProcessInfo"/>.
    /// </summary>
    /// <param name="processKey">Used to indicate the process that should be initialized.</param>
    /// <param name="parentProcessId">The parent Id of the process if one exists.</param>
    /// <param name="eventProxyStepId">An optional identifier of an actor requesting to proxy events.</param>
    /// <returns>A<see cref="Task"/></returns>
    Task InitializeProcessAsync(string processKey, string? parentProcessId, string? eventProxyStepId);

    /// <summary>
    /// Initializes the process with the specified process key.
    /// </summary>
    /// <param name="processKey"></param>
    /// <param name="processId"></param>
    /// <param name="parentProcessId"></param>
    /// <param name="eventProxyStepId"></param>
    /// <param name="processEvent"></param>
    /// <returns></returns>
    Task KeyedRunOnceAsync(string processKey, string processId, string parentProcessId, string? eventProxyStepId, string processEvent);

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
    Task RunOnceAsync(string processEvent);

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
    Task SendMessageAsync(string processEvent);

    /// <summary>
    /// Gets the process information.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcess"/></returns>
    Task<IDictionary<string, KernelProcessStepState>> GetProcessInfoAsync();
}

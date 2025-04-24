// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;

namespace Microsoft.SemanticKernel.Agents.Runtime.Core;

/// <summary>
/// Represents the core application hosting the agent runtime.
/// Manages the application lifecycle including startup, shutdown, and message publishing.
/// </summary>
public class AgentsApp
{
    private int _runningCount;

    /// <summary>
    /// Initializes a new instance of the <see cref="AgentsApp"/> class.
    /// </summary>
    /// <param name="host">The underlying application host.</param>
    internal AgentsApp(IHost host)
    {
        this.Host = host;
    }

    /// <summary>
    /// Gets the underlying host responsible for managing application lifetime.
    /// </summary>
    public IHost Host { get; }

    /// <summary>
    /// Gets the service provider for dependency resolution.
    /// </summary>
    public IServiceProvider Services => this.Host.Services;

    /// <summary>
    /// Gets the application lifetime object to manage startup and shutdown events.
    /// </summary>
    public IHostApplicationLifetime ApplicationLifetime => this.Services.GetRequiredService<IHostApplicationLifetime>();

    /// <summary>
    /// Gets the agent runtime responsible for handling agent messaging and operations.
    /// </summary>
    public IAgentRuntime AgentRuntime => this.Services.GetRequiredService<IAgentRuntime>();

    /// <summary>
    /// Starts the application by initiating the host.
    /// Throws an exception if the application is already running.
    /// </summary>
    public async ValueTask StartAsync()
    {
        if (Interlocked.Exchange(ref this._runningCount, 1) != 0)
        {
            throw new InvalidOperationException("Application is already running.");
        }

        await this.Host.StartAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Shuts down the application by stopping the host.
    /// Throws an exception if the application is not running.
    /// </summary>
    public async ValueTask ShutdownAsync()
    {
        if (Interlocked.Exchange(ref this._runningCount, 0) != 1)
        {
            throw new InvalidOperationException("Application is already stopped.");
        }

        await this.Host.StopAsync().ConfigureAwait(false);
    }

    /// <summary>
    /// Publishes a message to the specified topic.
    /// If the application is not running, it starts the host first.
    /// </summary>
    /// <typeparam name="TMessage">The type of the message being published.</typeparam>
    /// <param name="message">The message to publish.</param>
    /// <param name="topic">The topic to which the message will be published.</param>
    /// <param name="messageId">An optional unique identifier for the message.</param>
    /// <param name="cancellationToken">A token to cancel the operation if needed.</param>
    public async ValueTask PublishMessageAsync<TMessage>(TMessage message, TopicId topic, string? messageId = null, CancellationToken cancellationToken = default)
        where TMessage : notnull
    {
        if (Volatile.Read(ref this._runningCount) == 0)
        {
            await this.StartAsync().ConfigureAwait(false);
        }

        await this.AgentRuntime.PublishMessageAsync(message, topic, messageId: messageId, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Waits for the host to complete its shutdown process.
    /// </summary>
    /// <param name="cancellationToken">A token to cancel the operation if needed.</param>
    public Task WaitForShutdownAsync(CancellationToken cancellationToken = default)
    {
        return this.Host.WaitForShutdownAsync(cancellationToken);
    }
}

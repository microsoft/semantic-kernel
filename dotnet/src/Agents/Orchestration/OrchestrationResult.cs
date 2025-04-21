// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Runtime;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Represents the result of an orchestration operation that yields a value of type <typeparamref name="TValue"/>.
/// This class encapsulates the asynchronous completion of an orchestration process.
/// </summary>
/// <typeparam name="TValue">The type of the value produced by the orchestration.</typeparam>
public sealed class OrchestrationResult<TValue>
{
    private readonly string _orchestration;
    private readonly TaskCompletionSource<TValue> _completion;
    private readonly ILogger _logger;

    internal OrchestrationResult(string orchestration, TopicId topic, TaskCompletionSource<TValue> completion, ILogger logger)
    {
        this._orchestration = orchestration;
        this.Topic = topic;
        this._completion = completion;
        this._logger = logger;
    }

    /// <summary>
    /// Gets the topic identifier associated with this orchestration result.
    /// </summary>
    public TopicId Topic { get; }

    /// <summary>
    /// Asynchronously retrieves the orchestration result value.
    /// If a timeout is specified, the method will throw a <see cref="TimeoutException"/>
    /// if the orchestration does not complete within the allotted time.
    /// </summary>
    /// <param name="timeout">An optional <see cref="TimeSpan"/> representing the maximum wait duration.</param>
    /// <returns>A <see cref="ValueTask{TValue}"/> representing the result of the orchestration.</returns>
    /// <exception cref="TimeoutException">Thrown if the orchestration does not complete within the specified timeout period.</exception>
    public async ValueTask<TValue> GetValueAsync(TimeSpan? timeout = null)
    {
        this._logger.LogOrchestrationResultAwait(this._orchestration, this.Topic);

        if (timeout.HasValue)
        {
            Task[] tasks = { this._completion.Task };
            if (!Task.WaitAll(tasks, timeout.Value))
            {
                this._logger.LogOrchestrationResultTimeout(this._orchestration, this.Topic);
                throw new TimeoutException($"Orchestration did not complete within the allowed duration ({timeout}).");
            }
        }

        this._logger.LogOrchestrationResultComplete(this._orchestration, this.Topic);

        return await this._completion.Task.ConfigureAwait(false);
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Represents the result of an orchestration operation that yields a value of type <typeparamref name="TValue"/>.
/// This class encapsulates the asynchronous completion of an orchestration process.
/// </summary>
/// <typeparam name="TValue">The type of the value produced by the orchestration.</typeparam>
public sealed class OrchestrationResult<TValue>
{
    private readonly TaskCompletionSource<TValue> _completion;

    internal OrchestrationResult(TopicId topic, TaskCompletionSource<TValue> completion)
    {
        this.Topic = topic;
        this._completion = completion;
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
        Trace.WriteLine($"\n!!! ORCHESTRATION AWAIT: {this.Topic}\n");

        if (timeout.HasValue)
        {
            Task[] tasks = { this._completion.Task };
            if (!Task.WaitAll(tasks, timeout.Value))
            {
                throw new TimeoutException($"Orchestration did not complete within the allowed duration ({timeout}).");
            }
        }

        return await this._completion.Task.ConfigureAwait(false);
    }
}

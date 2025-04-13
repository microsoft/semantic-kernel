// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// %%% COMMENT
/// </summary>
/// <typeparam name="TValue"></typeparam>
public sealed class OrchestrationResult<TValue>
{
    private readonly TaskCompletionSource<TValue> _completion;

    internal OrchestrationResult(TopicId topic, TaskCompletionSource<TValue> completion)
    {
        this.Topic = topic;
        this._completion = completion;
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public TopicId Topic { get; }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <returns></returns>
    public async ValueTask<TValue> GetValueAsync(TimeSpan? timeout = null) // %%% TODO: TryGetValueAsync ???
    {
        Trace.WriteLine($"\n!!! ORCHESTRATION AWAIT: {this.Topic}\n");

        if (timeout.HasValue)
        {
            Task[] tasks = [this._completion.Task];
            if (!Task.WaitAll(tasks, timeout.Value))
            {
                throw new TimeoutException($"Orchestration did not complete within the allowed duration ({timeout})."); // %%% EXCEPTION TYPE
            }
        }

        return await this._completion.Task.ConfigureAwait(false);
    }
}

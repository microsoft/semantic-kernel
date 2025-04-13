// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.AgentRuntime.Core;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

public abstract partial class AgentOrchestration<TInput, TSource, TResult, TOutput>
{
    /// <summary>
    /// Actor responsible for receiving final message and transforming it into the output type.
    /// </summary>
    private sealed class RequestActor : PatternActor, IHandle<TInput>
    {
        private readonly Func<TInput, ValueTask<TSource>> _transform;
        private readonly Func<TSource, Task> _action;

        /// <summary>
        /// Initializes a new instance of the <see cref="AgentOrchestration{TInput, TSource, TResult, TOutput}"/> class.
        /// </summary>
        /// <param name="id">The unique identifier of the agent.</param>
        /// <param name="runtime">The runtime associated with the agent.</param>
        /// <param name="transform">A function that transforms an input of type TInput into a source type TSource.</param>
        /// <param name="action">An asynchronous function that processes the resulting source.</param>
        public RequestActor(
            AgentId id,
            IAgentRuntime runtime,
            Func<TInput, ValueTask<TSource>> transform,
            Func<TSource, Task> action)
            : base(id, runtime, $"{id.Type}_Actor")
        {
            this._transform = transform;
            this._action = action;
        }

        /// <summary>
        /// Handles the incoming message by transforming the input and executing the corresponding action asynchronously.
        /// </summary>
        /// <param name="item">The input message of type TInput.</param>
        /// <param name="messageContext">The context of the message, providing additional details.</param>
        /// <returns>A ValueTask representing the asynchronous operation.</returns>
        public async ValueTask HandleAsync(TInput item, MessageContext messageContext)
        {
            Trace.WriteLine($"> ORCHESTRATION ENTER: {this.Id.Type}");
            try
            {
                TSource source = await this._transform.Invoke(item).ConfigureAwait(false);
                await this._action.Invoke(source).ConfigureAwait(false);
            }
            catch (Exception exception)
            {
                Trace.WriteLine($"ERROR: {exception.Message}");
                // Log exception details and allow orchestration to fail
                throw;
            }
        }
    }
}

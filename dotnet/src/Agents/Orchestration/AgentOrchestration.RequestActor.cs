// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.AgentRuntime.Core;
using Microsoft.Extensions.Logging;

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
        /// <param name="logger">The logger to use for the actor</param>
        public RequestActor(
            AgentId id,
            IAgentRuntime runtime,
            Func<TInput, ValueTask<TSource>> transform,
            Func<TSource, Task> action,
            ILogger<RequestActor>? logger = null)
            : base(id, runtime, $"{id.Type}_Actor", logger)
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
            this.Logger.LogOrchestrationRequestInvoke(this.Id);
            try
            {
                TSource source = await this._transform.Invoke(item).ConfigureAwait(false);
                await this._action.Invoke(source).ConfigureAwait(false);
                Logger.LogOrchestrationStart(this.Id);
            }
            catch (Exception exception)
            {
                // Log exception details and allow orchestration to fail
                this.Logger.LogOrchestrationRequestFailure(this.Id, exception);
                throw;
            }
        }
    }
}

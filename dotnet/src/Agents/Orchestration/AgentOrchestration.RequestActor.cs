// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Orchestration.Transforms;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.Agents.Runtime.Core;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

public abstract partial class AgentOrchestration<TInput, TOutput>
{
    /// <summary>
    /// Actor responsible for receiving final message and transforming it into the output type.
    /// </summary>
    private sealed class RequestActor : OrchestrationActor, IHandle<TInput>
    {
        private readonly OrchestrationInputTransform<TInput> _transform;
        private readonly Func<IEnumerable<ChatMessageContent>, ValueTask> _action;
        private readonly TaskCompletionSource<TOutput> _completionSource;

        /// <summary>
        /// Initializes a new instance of the <see cref="AgentOrchestration{TInput, TOutput}"/> class.
        /// </summary>
        /// <param name="id">The unique identifier of the agent.</param>
        /// <param name="runtime">The runtime associated with the agent.</param>
        /// <param name="context">The orchestration context.</param>
        /// <param name="transform">A function that transforms an input of type TInput into a source type TSource.</param>
        /// <param name="completionSource">Optional TaskCompletionSource to signal orchestration completion.</param>
        /// <param name="action">An asynchronous function that processes the resulting source.</param>
        /// <param name="logger">The logger to use for the actor</param>
        public RequestActor(
            AgentId id,
            IAgentRuntime runtime,
            OrchestrationContext context,
            OrchestrationInputTransform<TInput> transform,
            TaskCompletionSource<TOutput> completionSource,
            Func<IEnumerable<ChatMessageContent>, ValueTask> action,
            ILogger<RequestActor>? logger = null)
            : base(id, runtime, context, $"{id.Type}_Actor", logger)
        {
            this._transform = transform;
            this._action = action;
            this._completionSource = completionSource;
        }

        /// <summary>
        /// Handles the incoming message by transforming the input and executing the corresponding action asynchronously.
        /// </summary>
        /// <param name="item">The input message of type TInput.</param>
        /// <param name="messageContext">The context of the message, providing additional details.</param>
        /// <returns>A ValueTask representing the asynchronous operation.</returns>
        public async ValueTask HandleAsync(TInput item, MessageContext messageContext)
        {
            this.Logger.LogOrchestrationRequestInvoke(this.Context.Orchestration, this.Id);
            try
            {
                IEnumerable<ChatMessageContent> input = await this._transform.Invoke(item).ConfigureAwait(false);
                Task task = this._action.Invoke(input).AsTask();
                this.Logger.LogOrchestrationStart(this.Context.Orchestration, this.Id);
                await task.ConfigureAwait(false);
            }
            catch (Exception exception) when (!exception.IsCriticalException())
            {
                // Log exception details and allow orchestration to fail
                this.Logger.LogOrchestrationRequestFailure(this.Context.Orchestration, this.Id, exception);
                this._completionSource.SetException(exception);
                throw;
            }
        }
    }
}

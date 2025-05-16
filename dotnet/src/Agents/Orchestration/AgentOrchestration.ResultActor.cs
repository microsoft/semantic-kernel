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
    /// Actor responsible for receiving the resultant message, transforming it, and handling further orchestration.
    /// </summary>
    private sealed class ResultActor<TResult> : OrchestrationActor, IHandle<TResult>
    {
        private readonly TaskCompletionSource<TOutput> _completionSource;
        private readonly OrchestrationResultTransform<TResult> _transformResult;
        private readonly OrchestrationOutputTransform<TOutput> _transform;

        /// <summary>
        /// Initializes a new instance of the <see cref="AgentOrchestration{TInput, TOutput}.ResultActor{TResult}"/> class.
        /// </summary>
        /// <param name="id">The unique identifier of the agent.</param>
        /// <param name="runtime">The runtime associated with the agent.</param>
        /// <param name="context">The orchestration context.</param>
        /// <param name="transformResult">A delegate that transforms a TResult instance into a ChatMessageContent.</param>
        /// <param name="transformOutput">A delegate that transforms a ChatMessageContent into a TOutput instance.</param>
        /// <param name="completionSource">Optional TaskCompletionSource to signal orchestration completion.</param>
        /// <param name="logger">The logger to use for the actor</param>
        public ResultActor(
            AgentId id,
            IAgentRuntime runtime,
            OrchestrationContext context,
            OrchestrationResultTransform<TResult> transformResult,
            OrchestrationOutputTransform<TOutput> transformOutput,
            TaskCompletionSource<TOutput> completionSource,
            ILogger<ResultActor<TResult>>? logger = null)
            : base(id, runtime, context, $"{id.Type}_Actor", logger)
        {
            this._completionSource = completionSource;
            this._transformResult = transformResult;
            this._transform = transformOutput;
        }

        /// <summary>
        /// Processes the received TResult message by transforming it into a TOutput message.
        /// If a CompletionTarget is defined, it sends the transformed message to the corresponding agent.
        /// Additionally, it signals completion via the provided TaskCompletionSource if available.
        /// </summary>
        /// <param name="item">The result item to process.</param>
        /// <param name="messageContext">The context associated with the message.</param>
        /// <returns>A ValueTask representing asynchronous operation.</returns>
        public async ValueTask HandleAsync(TResult item, MessageContext messageContext)
        {
            this.Logger.LogOrchestrationResultInvoke(this.Context.Orchestration, this.Id);

            try
            {
                if (!this._completionSource.Task.IsCompleted)
                {
                    IList<ChatMessageContent> result = this._transformResult.Invoke(item);
                    TOutput output = await this._transform.Invoke(result).ConfigureAwait(false);
                    this._completionSource.TrySetResult(output);
                }
            }
            catch (Exception exception)
            {
                // Log exception details and fail orchestration as per design.
                this.Logger.LogOrchestrationResultFailure(this.Context.Orchestration, this.Id, exception);
                this._completionSource.SetException(exception);
                throw;
            }
        }
    }
}

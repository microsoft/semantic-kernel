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
    /// Actor responsible for receiving the resultant message, transforming it, and handling further orchestration.
    /// </summary>
    private sealed class ResultActor : PatternActor, IHandle<TResult>
    {
        private readonly TaskCompletionSource<TOutput>? _completionSource;
        private readonly Func<TResult, ValueTask<TOutput>> _transform;

        /// <summary>
        /// Initializes a new instance of the <see cref="AgentOrchestration{TInput, TSource, TResult, TOutput}.ResultActor"/> class.
        /// </summary>
        /// <param name="id">The unique identifier of the agent.</param>
        /// <param name="runtime">The runtime associated with the agent.</param>
        /// <param name="transform">A delegate that transforms a TResult instance into a TOutput instance.</param>
        /// <param name="completionSource">Optional TaskCompletionSource to signal orchestration completion.</param>
        /// <param name="logger">The logger to use for the actor</param>
        public ResultActor(
            AgentId id,
            IAgentRuntime runtime,
            Func<TResult, ValueTask<TOutput>> transform,
            TaskCompletionSource<TOutput>? completionSource = null,
            ILogger<RequestActor>? logger = null)
            : base(id, runtime, $"{id.Type}_Actor", logger)
        {
            this._completionSource = completionSource;
            this._transform = transform;
        }

        /// <summary>
        /// Gets or sets the optional target agent type to which the output message is forwarded.
        /// </summary>
        public AgentType? CompletionTarget { get; init; }

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
            this.Logger.LogOrchestrationResultInvoke(this.Id);

            try
            {
                TOutput output = await this._transform.Invoke(item).ConfigureAwait(false);

                if (this.CompletionTarget.HasValue)
                {
                    await this.SendMessageAsync(output!, this.CompletionTarget.Value, messageContext.CancellationToken).ConfigureAwait(false);
                }

                this._completionSource?.SetResult(output);
            }
            catch (Exception exception)
            {
                // Log exception details and fail orchestration as per design.
                this.Logger.LogOrchestrationResultFailure(this.Id, exception);
                throw;
            }
        }
    }
}

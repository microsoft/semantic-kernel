// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.AgentRuntime;
using Microsoft.AgentRuntime.Core;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// An actor that represents the orchestration.
/// </summary>
public abstract partial class AgentOrchestration<TInput, TSource, TResult, TOutput>
{
    private sealed class ResultActor : BaseAgent, IHandle<TResult>
    {
        private readonly TaskCompletionSource<TOutput>? _completionSource;
        private readonly Func<TResult, TOutput> _transform;

        /// <summary>
        /// Initializes a new instance of the <see cref="AgentActor"/> class.
        /// </summary>
        /// <param name="id">The unique identifier of the agent.</param>
        /// <param name="runtime">The runtime associated with the agent.</param>
        /// <param name="transform">// %%% COMMENT</param>
        /// <param name="completionSource">Signals completion.</param>
        public ResultActor(
            AgentId id,
            IAgentRuntime runtime,
            Func<TResult, TOutput> transform,
            TaskCompletionSource<TOutput>? completionSource = null)
            : base(id, runtime, $"{id.Type}_Actor")
        {
            this._completionSource = completionSource;
            this._transform = transform;
        }

        /// <summary>
        /// %%% COMMENT
        /// </summary>
        public AgentType? CompletionTarget { get; init; }

        /// <summary>
        /// %%% COMMENT
        /// </summary>
        /// <param name="item"></param>
        /// <param name="messageContext"></param>
        /// <returns></returns>
        public async ValueTask HandleAsync(TResult item, MessageContext messageContext)
        {
            Trace.WriteLine($"> ORCHESTRATION EXIT: {this.Id.Type}");

            try
            {
                TOutput output = this._transform.Invoke(item);

                if (this.CompletionTarget != null)
                {
                    await this.SendMessageAsync(output!, new AgentId(this.CompletionTarget, AgentId.DefaultKey)).ConfigureAwait(false); // %%% AGENTID && NULL OVERRIDE
                }

                this._completionSource?.SetResult(output);
            }
            catch (Exception exception)
            {
                Trace.WriteLine($"ERROR: {exception.Message}");
                throw; // %%% EXCEPTION
            }
        }
    }
}

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
    private sealed class RequestActor : BaseAgent, IHandle<TInput>
    {
        private readonly Func<TInput, TSource> _transform;
        private readonly Func<TSource, Task> _action;

        /// <summary>
        /// Initializes a new instance of the <see cref="AgentActor"/> class.
        /// </summary>
        /// <param name="id">The unique identifier of the agent.</param>
        /// <param name="runtime">The runtime associated with the agent.</param>
        /// <param name="transform">// %%% COMMENT</param>
        /// <param name="action">// %%% COMMENT</param>
        public RequestActor(
            AgentId id,
            IAgentRuntime runtime,
            Func<TInput, TSource> transform,
            Func<TSource, Task> action)
            : base(id, runtime, $"{id.Type}_Actor")
        {
            this._transform = transform;
            this._action = action;
        }

        /// <summary>
        /// %%% COMMENT
        /// </summary>
        /// <param name="item"></param>
        /// <param name="messageContext"></param>
        /// <returns></returns>
        public async ValueTask HandleAsync(TInput item, MessageContext messageContext)
        {
            Trace.WriteLine($"> ORCHESTRATION ENTER: {this.Id.Type}");
            try
            {
                TSource source = this._transform.Invoke(item);
                await this._action.Invoke(source).ConfigureAwait(false);
            }
            catch (Exception exception)
            {
                Trace.WriteLine($"ERROR: {exception.Message}");
                throw; // %%% EXCEPTION
            }
        }
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Agents.Runtime;
using Microsoft.SemanticKernel.Agents.Runtime.Core;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Handoff;

/// <summary>
/// An actor used with the <see cref="HandoffOrchestration{TInput,TOutput}"/>.
/// </summary>
internal sealed class HandoffActor :
    AgentActor,
    IHandle<HandoffMessages.InputTask>,
    IHandle<HandoffMessages.Request>,
    IHandle<HandoffMessages.Response>
{
    private readonly HandoffLookup _handoffs;
    private readonly AgentType _resultHandoff;
    private readonly List<ChatMessageContent> _cache;

    /// <summary>
    /// Initializes a new instance of the <see cref="HandoffActor"/> class.
    /// </summary>
    /// <param name="id">The unique identifier of the agent.</param>
    /// <param name="runtime">The runtime associated with the agent.</param>
    /// <param name="context">The orchestration context.</param>
    /// <param name="agent">An <see cref="Agent"/>.</param>
    /// <param name="handoffs">The handoffs available to this agent</param>
    /// <param name="resultHandoff">The handoff agent for capturing the result.</param>
    /// <param name="logger">The logger to use for the actor</param>
    public HandoffActor(AgentId id, IAgentRuntime runtime, OrchestrationContext context, Agent agent, HandoffLookup handoffs, AgentType resultHandoff, ILogger<HandoffActor>? logger = null)
        : base(id, runtime, context, agent, logger)
    {
        this._cache = [];
        this._handoffs = handoffs;
        this._resultHandoff = resultHandoff;
    }

    /// <inheritdoc/>
    protected override AgentInvokeOptions? CreateInvokeOptions()
    {
        // Clone kernel to avoid modifying the original
        Kernel kernel = this.Agent.Kernel.Clone();
        kernel.AutoFunctionInvocationFilters.Add(new HandoffInvocationFilter());
        kernel.Plugins.Add(this.CreateHandoffPlugin());

        // Create invocation options that use auto-function invocation and our modified kernel.
        AgentInvokeOptions options =
            new()
            {
                Kernel = kernel,
                KernelArguments = new(new PromptExecutionSettings { FunctionChoiceBehavior = FunctionChoiceBehavior.Auto() })
            };

        return options;
    }

    /// <inheritdoc/>
    public ValueTask HandleAsync(HandoffMessages.InputTask item, MessageContext messageContext)
    {
        this._cache.AddRange(item.Messages);

        return this.HandleAsync(messageContext.CancellationToken);
    }

    /// <inheritdoc/>
    public ValueTask HandleAsync(HandoffMessages.Request item, MessageContext messageContext) => this.HandleAsync(messageContext.CancellationToken);

    /// <inheritdoc/>
    public ValueTask HandleAsync(HandoffMessages.Response item, MessageContext messageContext)
    {
        this._cache.Add(item.Message);

        return ValueTask.CompletedTask;
    }

    private async ValueTask HandleAsync(CancellationToken cancellationToken)
    {
        this.Logger.LogHandoffAgentInvoke(this.Id);

        ChatMessageContent response = await this.InvokeAsync(this._cache, cancellationToken).ConfigureAwait(false);
        this._cache.Clear();

        this.Logger.LogHandoffAgentResult(this.Id, response.Content);

        await this.PublishMessageAsync(new HandoffMessages.Response { Message = response }, this.Context.Topic, messageId: null, cancellationToken).ConfigureAwait(false);
    }

    private KernelPlugin CreateHandoffPlugin()
    {
        return KernelPluginFactory.CreateFromFunctions(HandoffInvocationFilter.HandoffPlugin, CreateHandoffFunctions());

        IEnumerable<KernelFunction> CreateHandoffFunctions()
        {
            yield return KernelFunctionFactory.CreateFromMethod(
                this.EndAsync,
                functionName: "end_task_with_summary",
                description: "End the task with a summary when there is no further action to take.");

            foreach ((string name, (AgentType type, string description)) in this._handoffs)
            {
                KernelFunction kernelFunction =
                    KernelFunctionFactory.CreateFromMethod(
                        (CancellationToken cancellationToken) => this.HandoffAsync(type, cancellationToken),
                        functionName: $"transfer_to_{name}",
                        description: description);

                yield return kernelFunction;
            }
        }
    }

    private async ValueTask HandoffAsync(AgentType agentType, CancellationToken cancellationToken = default)
    {
        this.Logger.LogHandoffFunctionCall(this.Id, agentType);
        await this.SendMessageAsync(new HandoffMessages.Request(), agentType, cancellationToken).ConfigureAwait(false);
    }

    private async ValueTask EndAsync(string summary, CancellationToken cancellationToken)
    {
        this.Logger.LogHandoffSummary(this.Id, summary);
        await this.SendMessageAsync(new HandoffMessages.Result { Message = new ChatMessageContent(AuthorRole.User, summary) }, this._resultHandoff, cancellationToken).ConfigureAwait(false);
    }
}

internal sealed class HandoffInvocationFilter() : IAutoFunctionInvocationFilter
{
    public const string HandoffPlugin = nameof(HandoffPlugin);

    public async Task OnAutoFunctionInvocationAsync(AutoFunctionInvocationContext context, Func<AutoFunctionInvocationContext, Task> next)
    {
        // Execution the function
        await next(context).ConfigureAwait(false);

        // Signal termination if the function is part of the handoff plugin
        if (context.Function.PluginName == HandoffPlugin)
        {
            context.Terminate = true;
        }
    }
}

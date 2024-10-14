// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Step04.Models;

namespace Step04.Steps;

/// <summary>
/// %%%
/// </summary>
public class WorkerAgentStep : AgentProcessStep<ChatCompletionAgent>
{
    public const string AgentServiceKey = nameof(ManagerAgentStep);

    public static class Functions
    {
        public const string InvokeAgent = nameof(InvokeAgent);
    }

    /// <inheritdoc/>
    protected override string ServiceKey => AgentServiceKey;

    [KernelFunction(Functions.InvokeAgent)]
    public async Task InvokeAgentAsync(KernelProcessStepContext context, List<ChatMessageContent> input, Kernel kernel)
    {
        ChatCompletionAgent agent = this.GetAgent(kernel);
        //ChatHistory history = kernel.GetHistory();

        ChatMessageContent[] response = [..input, new(AuthorRole.Assistant, "YOU GOT IT, BOSS!") { AuthorName = "DUDE" }];

        await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.AgentResponded, Data = response });
    }
}

// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.History;
using Microsoft.SemanticKernel.ChatCompletion;
using Step04.Models;

namespace Step04.Steps;

/// <summary>
/// %%%
/// </summary>
public class ManagerAgentStep : AgentProcessStep<ChatCompletionAgent>
{
    public const string AgentServiceKey = nameof(ManagerAgentStep);

    public static class Functions
    {
        public const string InvokeAgent = nameof(InvokeAgent);
        public const string ProcessResponse = nameof(ProcessResponse);
    }

    /// <inheritdoc/>
    protected override string ServiceKey => AgentServiceKey;

    [KernelFunction(Functions.InvokeAgent)]
    public async Task InvokeAgentAsync(KernelProcessStepContext context, string userInput, Kernel kernel)
    {
        ChatHistory history = kernel.GetHistory();

        ChatCompletionAgent agent = this.GetAgent(kernel);

        List<ChatMessageContent> response = [];
        await foreach (ChatMessageContent message in agent.InvokeAsync(history))
        {
            response.Add(message);
        }
        history.AddRange(response);
        if (history.Count == 4)
        {
            await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.ManagerAgentWorking, Data = response });
        }
        else
        {
            await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.AgentResponded, Data = response });
        }
    }

    [KernelFunction(Functions.ProcessResponse)]
    public async Task ProcessResponseAsync(KernelProcessStepContext context, ChatMessageContent[] chat, Kernel kernel)
    {
        ChatHistorySummarizationReducer reducer = new(kernel.GetRequiredService<IChatCompletionService>(), 1);
        IEnumerable<ChatMessageContent>? reducedResponse = await reducer.ReduceAsync(chat);
        ChatMessageContent summary = reducedResponse == null ? chat.Last() : reducedResponse.First();
        summary.AuthorName = GetAgent(kernel).Name; // %%% CONSTANT or MEMBER

        ChatMessageContent[] response = [summary];
        ChatHistory history = kernel.GetHistory();
        history.AddRange(response);

        await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.AgentResponded, Data = response });
    }
}

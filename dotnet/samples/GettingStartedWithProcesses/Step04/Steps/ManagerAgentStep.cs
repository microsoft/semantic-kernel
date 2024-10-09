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
public class ManagerAgentStep : KernelProcessStep<ChatHistory>
{
    public static class Functions
    {
        public const string InvokeAgent = nameof(InvokeAgent);
        public const string ProcessResponse = nameof(ProcessResponse);
    }

    private readonly ChatHistory _history = [];
    private ChatCompletionAgent _agent;

    /// <inheritdoc/>
    public override ValueTask ActivateAsync(KernelProcessStepState<ChatHistory> state)
    {
        state.State = this._history; // %%% ???
        return ValueTask.CompletedTask;
    }

    [KernelFunction(Functions.InvokeAgent)]
    public async Task InvokeAgentAsync(KernelProcessStepContext context, string userInput, Kernel kernel)
    {
        this._history.Add(new ChatMessageContent(AuthorRole.User, userInput));

        ChatCompletionAgent agent = this.GetAgent(kernel); // %%% HACK

        List<ChatMessageContent> response = [];
        await foreach (ChatMessageContent message in agent.InvokeAsync(this._history))
        {
            response.Add(message);
        }
        this._history.AddRange(response);
        if (this._history.Count == 4)
        {
            await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.ManagerAgentWorking, Data = response });
        }
        else
        {
            await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.ManagerAgentResponded, Data = response });
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
        this._history.AddRange(response);

        await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.ManagerAgentResponded, Data = response });
    }

    public ChatCompletionAgent GetAgent(Kernel kernel)
    {
        return
           this._agent ??=
           new ChatCompletionAgent()
           {
               Name = "Manager",
               //Instructions = "%% TBD",
               Kernel = kernel,
           };

    }

    //public ManagerAgentStep(Kernel kernel)
    //{
    //    this._agent =
    //       new ChatCompletionAgent()
    //       {
    //           Name = "Manager",
    //           //Instructions = "%% TBD",
    //           Kernel = kernel,
    //       };

    //}
}

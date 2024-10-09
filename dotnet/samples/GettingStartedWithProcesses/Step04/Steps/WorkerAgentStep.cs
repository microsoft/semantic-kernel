// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Step04.Models;

namespace Step04.Steps;

/// <summary>
/// %%%
/// </summary>
public class WorkerAgentStep : KernelProcessStep<ChatHistory>
{
    public static class Functions
    {
        public const string InvokeAgent = nameof(InvokeAgent);
    }

    //private readonly ChatHistory _history = [];
    //private ChatCompletionAgent _agent;

    ///// <inheritdoc/>
    //public override ValueTask ActivateAsync(KernelProcessStepState<ChatHistory> state)
    //{
    //    state.State = this._history; // %%% ???
    //    return ValueTask.CompletedTask;
    //}

    [KernelFunction(Functions.InvokeAgent)]
    public async Task InvokeAgentAsync(KernelProcessStepContext context, List<ChatMessageContent> input, Kernel kernel)
    {
        throw new Exception();
        ChatMessageContent[] response = [..input, new(AuthorRole.Assistant, "YOU GOT IT, BOSS!") { AuthorName = "DUDE" }];

        //ChatCompletionAgent agent = this.GetAgent(kernel); // %%% HACK

        //List<ChatMessageContent> response = [];
        //await foreach (ChatMessageContent message in agent.InvokeAsync(this._history))
        //{
        //    response.Add(message);
        //}
        //this._history.AddRange(response);
        await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.WorkerAgentResponded, Data = response });
        //await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.ManagerAgentWorking, Data = response });
    }

    //public ChatCompletionAgent GetAgent(Kernel kernel)
    //{
    //    return
    //       this._agent ??=
    //       new ChatCompletionAgent()
    //       {
    //           Name = "Manager",
    //           //Instructions = "%% TBD",
    //           Kernel = kernel,
    //       };

    //}
}

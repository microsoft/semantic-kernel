// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Step04.Steps;

/// <summary>
/// This steps defines actions for the group chat in which to agents collaborate in
/// response to input from the primary agent.
/// </summary>
public class AgentGroupChatStep : KernelProcessStep
{
    public const string ChatServiceKey = $"{nameof(AgentGroupChatStep)}:{nameof(ChatServiceKey)}";
    public const string ReducerServiceKey = $"{nameof(AgentGroupChatStep)}:{nameof(ReducerServiceKey)}";

    public static class ProcessStepFunctions
    {
        public const string InvokeAgentGroup = nameof(InvokeAgentGroup);
    }

    [KernelFunction(ProcessStepFunctions.InvokeAgentGroup)]
    public async Task InvokeAgentGroupAsync(KernelProcessStepContext context, Kernel kernel, string input)
    {
        AgentGroupChat chat = kernel.GetRequiredService<AgentGroupChat>();

        // Reset chat state from previous invocation
        //await chat.ResetAsync();
        chat.IsComplete = false;

        ChatMessageContent message = new(AuthorRole.User, input);
        chat.AddChatMessage(message);
        await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.GroupMessage, Data = message });

        await foreach (ChatMessageContent response in chat.InvokeAsync())
        {
            await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.GroupMessage, Data = response });
        }

        ChatMessageContent[] history = await chat.GetChatMessagesAsync().Reverse().ToArrayAsync();

        // Summarize the group chat as a response to the primary agent
        string summary = await kernel.SummarizeHistoryAsync(ReducerServiceKey, history);

        await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.GroupCompleted, Data = summary });
    }
}

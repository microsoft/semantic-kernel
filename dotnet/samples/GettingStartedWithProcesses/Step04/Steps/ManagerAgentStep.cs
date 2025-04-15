// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using System.Text.Json;
using Events;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;

namespace Step04.Steps;

/// <summary>
/// This steps defines actions for the primary agent.  This agent is responsible forinteracting with
/// the user as well as as delegating to a group of agents.
/// </summary>
public class ManagerAgentStep : KernelProcessStep
{
    public const string AgentServiceKey = $"{nameof(ManagerAgentStep)}:{nameof(AgentServiceKey)}";
    public const string ReducerServiceKey = $"{nameof(ManagerAgentStep)}:{nameof(ReducerServiceKey)}";

    public static class Functions
    {
        public const string InvokeAgent = nameof(InvokeAgent);
        public const string InvokeGroup = nameof(InvokeGroup);
        public const string ReceiveResponse = nameof(ReceiveResponse);
    }

    [KernelFunction(Functions.InvokeAgent)]
    public async Task InvokeAgentAsync(KernelProcessStepContext context, Kernel kernel, string userInput, ILogger logger)
    {
        // Get the chat history
        IChatHistoryProvider historyProvider = kernel.GetHistory();
        ChatHistory history = await historyProvider.GetHistoryAsync();
        ChatHistoryAgentThread agentThread = new(history);

        // Obtain the agent response
        ChatCompletionAgent agent = kernel.GetAgent<ChatCompletionAgent>(AgentServiceKey);
        await foreach (ChatMessageContent message in agent.InvokeAsync(new ChatMessageContent(AuthorRole.User, userInput), agentThread))
        {
            // Both the input message and response message will automatically be added to the thread, which will update the internal chat history.

            // Emit event for each agent response
            await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.AgentResponse, Data = message });
        }

        // Commit any changes to the chat history
        await historyProvider.CommitAsync();

        // Evaluate current intent
        IntentResult intent = await IsRequestingUserInputAsync(kernel, history, logger);

        string intentEventId =
            intent.IsRequestingUserInput ?
                AgentOrchestrationEvents.AgentResponded :
                intent.IsWorking ?
                    AgentOrchestrationEvents.AgentWorking :
                    CommonEvents.UserInputComplete;

        await context.EmitEventAsync(new() { Id = intentEventId });
    }

    [KernelFunction(Functions.InvokeGroup)]
    public async Task InvokeGroupAsync(KernelProcessStepContext context, Kernel kernel)
    {
        // Get the chat history
        IChatHistoryProvider historyProvider = kernel.GetHistory();
        ChatHistory history = await historyProvider.GetHistoryAsync();

        // Summarize the conversation with the user to use as input to the agent group
        string summary = await kernel.SummarizeHistoryAsync(ReducerServiceKey, history);

        await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.GroupInput, Data = summary });
    }

    [KernelFunction(Functions.ReceiveResponse)]
    public async Task ReceiveResponseAsync(KernelProcessStepContext context, Kernel kernel, string response)
    {
        // Get the chat history
        IChatHistoryProvider historyProvider = kernel.GetHistory();
        ChatHistory history = await historyProvider.GetHistoryAsync();

        // Proxy the inner response
        ChatCompletionAgent agent = kernel.GetAgent<ChatCompletionAgent>(AgentServiceKey);
        ChatMessageContent message = new(AuthorRole.Assistant, response) { AuthorName = agent.Name };
        history.Add(message);

        await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.AgentResponse, Data = message });

        await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.AgentResponded });
    }

    private static async Task<IntentResult> IsRequestingUserInputAsync(Kernel kernel, ChatHistory history, ILogger logger)
    {
        ChatHistory localHistory =
        [
            new ChatMessageContent(AuthorRole.System, "Analyze the conversation and determine if user input is being solicited."),
            .. history.TakeLast(1)
        ];

        IChatCompletionService service = kernel.GetRequiredService<IChatCompletionService>();

        ChatMessageContent response = await service.GetChatMessageContentAsync(localHistory, new OpenAIPromptExecutionSettings { ResponseFormat = typeof(IntentResult) });
        IntentResult intent = JsonSerializer.Deserialize<IntentResult>(response.ToString())!;

        logger.LogTrace("{StepName} Response Intent - {IsRequestingUserInput}: {Rationale}", nameof(ManagerAgentStep), intent.IsRequestingUserInput, intent.Rationale);

        return intent;
    }

    [DisplayName("IntentResult")]
    [Description("this is the result description")]
    public sealed record IntentResult(
        [property:Description("True if user input is requested or solicited.  Addressing the user with no specific request is False.  Asking a question to the user is True.")]
        bool IsRequestingUserInput,
        [property:Description("True if the user request is being worked on.")]
        bool IsWorking,
        [property:Description("Rationale for the value assigned to IsRequestingUserInput")]
        string Rationale);
}

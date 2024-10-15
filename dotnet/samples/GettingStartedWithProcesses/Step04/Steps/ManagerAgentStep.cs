// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.OpenAI;
using ChatResponseFormat = OpenAI.Chat.ChatResponseFormat;

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

        // Add the user input to the chat history
        history.Add(new ChatMessageContent(AuthorRole.User, userInput));

        // Obtain the agent response
        ChatCompletionAgent agent = kernel.GetAgent<ChatCompletionAgent>(AgentServiceKey);
        await foreach (ChatMessageContent message in agent.InvokeAsync(await historyProvider.GetHistoryAsync()))
        {
            // Capture each response
            history.Add(message);

            // Emit event for each agent response
            await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.AgentResponse, Data = message });
        }

        // Commit any changes to the chat history
        await historyProvider.CommitAsync();

        bool requireUserResponse = await IsRequestingUserInputAsync(kernel, history, logger);

        string finalEventId = requireUserResponse ? AgentOrchestrationEvents.AgentResponded : AgentOrchestrationEvents.AgentWorking;
        await context.EmitEventAsync(new() { Id = finalEventId });
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

        ChatMessageContent message = new(AuthorRole.Assistant, response) { AuthorName = "Group" };
        history.Add(new ChatMessageContent(AuthorRole.Assistant, response) { AuthorName = "Group" }); // %%% PLACE HOLDER
        await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.AgentResponse, Data = message }); // %%% PLACE HOLDER

        await context.EmitEventAsync(new() { Id = AgentOrchestrationEvents.AgentResponded });
    }

    private static async Task<bool> IsRequestingUserInputAsync(Kernel kernel, ChatHistory history, ILogger logger)
    {
        ChatHistory localHistory =
        [
            new ChatMessageContent(AuthorRole.System, "Analyze the conversation and determine if user input is being solicited."),
            ..history.TakeLast(2)
        ];

        IChatCompletionService service = kernel.GetRequiredService<IChatCompletionService>();

        ChatMessageContent response = await service.GetChatMessageContentAsync(localHistory, new OpenAIPromptExecutionSettings { ResponseFormat = s_intentResponseFormat });
        IntentResult intent = JsonSerializer.Deserialize<IntentResult>(response.ToString())!;

        logger.LogTrace("{StepName} Response Intent - {IsRequestingUserInput}: {Rationale}", nameof(ManagerAgentStep), intent.IsRequestingUserInput, intent.Rationale);
        //Console.WriteLine($"\t{intent.IsRequestingUserInput}:{Environment.NewLine}\t{intent.Rationale}"); // %%% REMOVE

        return intent.IsRequestingUserInput;
    }

    //    "IsUserDone": {
    //    "type": "boolean",
    //    "description": "True if user has indicated they having finished the interaction."
    //},

    private static readonly ChatResponseFormat s_intentResponseFormat = ChatResponseFormat.CreateJsonSchemaFormat(
        jsonSchemaFormatName: "intent_result",
        jsonSchema: BinaryData.FromString(
        """
        {
            "type": "object",
            "properties": {
                "IsRequestingUserInput": {
                    "type": "boolean",
                    "description": "True if user input is requested or solicited.  Addressing the user with no specific request is False.  Asking a question to the user is True."
                },
                "Rationale": {
                    "type": "string",
                    "description": "Rationale for the value assigned to IsRequestingUserInput"
                }
            },
            "required": ["IsRequestingUserInput", "Rationale"],
            "additionalProperties": false
        }
        """),
        jsonSchemaIsStrict: true);

    private sealed class IntentResult
    {
        public bool IsRequestingUserInput { get; set; }
        public string Rationale { get; set; }
    }
}

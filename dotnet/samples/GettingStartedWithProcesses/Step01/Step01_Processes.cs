﻿// Copyright (c) Microsoft. All rights reserved.

using Events;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using SharedSteps;

namespace Step01;

/// <summary>
/// Demonstrate creation of <see cref="KernelProcess"/> and
/// eliciting its response to three explicit user messages.
/// </summary>
public class Step01_Processes(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
{
    /// <summary>
    /// Demonstrates the creation of a simple process that has multiple steps, takes
    /// user input, interacts with the chat completion service, and demonstrates cycles
    /// in the process.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task UseSimpleProcessAsync()
    {
        // Create a kernel with a chat completion service
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Create a process that will interact with the chat completion service
        ProcessBuilder process = new("ChatBot");
        var introStep = process.AddStepFromType<IntroStep>();
        var userInputStep = process.AddStepFromType<ChatUserInputStep>();
        var responseStep = process.AddStepFromType<ChatBotResponseStep>();

        // Define the behavior when the process receives an external event
        process
            .OnExternalEvent(ChatBotEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(introStep));

        // When the intro is complete, notify the userInput step
        introStep
            .OnFunctionResult(nameof(IntroStep.PrintIntroMessage))
            .SendEventTo(new ProcessFunctionTargetBuilder(userInputStep));

        // When the userInput step emits an exit event, send it to the end steprt
        userInputStep
            .OnFunctionResult("GetUserInput")
            .StopProcess();

        // When the userInput step emits a user input event, send it to the assistantResponse step
        userInputStep
            .OnEvent(CommonEvents.UserInputReceived)
            .SendEventTo(new ProcessFunctionTargetBuilder(responseStep, parameterName: "userMessage"));

        // When the assistantResponse step emits a response, send it to the userInput step
        responseStep
            .OnEvent(ChatBotEvents.AssistantResponseGenerated)
            .SendEventTo(new ProcessFunctionTargetBuilder(userInputStep));

        // Build the process to get a handle that can be started
        KernelProcess kernelProcess = process.Build();

        // Start the process with an initial external event
        var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent() { Id = ChatBotEvents.StartProcess, Data = null });
    }

    /// <summary>
    /// The simplest implementation of a process step. IntroStep
    /// </summary>
    private sealed class IntroStep : KernelProcessStep
    {
        /// <summary>
        /// Prints an introduction message to the console.
        /// </summary>
        [KernelFunction]
        public void PrintIntroMessage()
        {
            System.Console.WriteLine("Welcome to Processes in Semantic Kernel.\n");
        }
    }

    /// <summary>
    /// A step that elicits user input.
    /// </summary>
    private sealed class ChatUserInputStep : ScriptedUserInputStep
    {
        public override void PopulateUserInputs()
        {
            if (_state != null)
            {
                _state.UserInputs.Add("Hello");
                _state.UserInputs.Add("How tall is the tallest mountain?");
                _state.UserInputs.Add("How low is the lowest valley?");
                _state.UserInputs.Add("How wide is the widest river?");
                _state.UserInputs.Add("exit");
            }
        }
    }

    /// <summary>
    /// A step that takes the user input from a previous step and generates a response from the chat completion service.
    /// </summary>
    private sealed class ChatBotResponseStep : KernelProcessStep<ChatBotState>
    {
        public static class Functions
        {
            public const string GetChatResponse = nameof(GetChatResponse);
        }

        /// <summary>
        /// The internal state object for the chat bot response step.
        /// </summary>
        internal ChatBotState? _state;

        /// <summary>
        /// ActivateAsync is the place to initialize the state object for the step.
        /// </summary>
        /// <param name="state">An instance of <see cref="ChatBotState"/></param>
        /// <returns>A <see cref="ValueTask"/></returns>
        public override ValueTask ActivateAsync(KernelProcessStepState<ChatBotState> state)
        {
            _state = state.State ?? new();
            _state.ChatMessages ??= new();
            return ValueTask.CompletedTask;
        }

        /// <summary>
        /// Generates a response from the chat completion service.
        /// </summary>
        /// <param name="context">The context for the current step and process. <see cref="KernelProcessStepContext"/></param>
        /// <param name="userMessage">The user message from a previous step.</param>
        /// <param name="_kernel">A <see cref="Kernel"/> instance.</param>
        /// <returns></returns>
        [KernelFunction(Functions.GetChatResponse)]
        public async Task GetChatResponseAsync(KernelProcessStepContext context, string userMessage, Kernel _kernel)
        {
            _state!.ChatMessages.Add(new(AuthorRole.User, userMessage));
            IChatCompletionService chatService = _kernel.Services.GetRequiredService<IChatCompletionService>();
            ChatMessageContent response = await chatService.GetChatMessageContentAsync(_state.ChatMessages).ConfigureAwait(false);
            if (response == null)
            {
                throw new InvalidOperationException("Failed to get a response from the chat completion service.");
            }

            System.Console.ForegroundColor = ConsoleColor.Yellow;
            System.Console.Write("Assistant: ");
            System.Console.ResetColor();
            System.Console.WriteLine(response.Content);

            // Update state with the response
            _state.ChatMessages.Add(response);

            // emit event: assistantResponse
            await context.EmitEventAsync(new KernelProcessEvent { Id = ChatBotEvents.AssistantResponseGenerated, Data = response });
        }
    }

    /// <summary>
    /// The state object for the <see cref="ChatBotResponseStep"/>.
    /// </summary>
    private sealed class ChatBotState
    {
        internal ChatHistory ChatMessages { get; set; } = new();
    }

    /// <summary>
    /// A class that defines the events that can be emitted by the chat bot process. This is
    /// not required but used to ensure that the event names are consistent.
    /// </summary>
    private static class ChatBotEvents
    {
        public const string StartProcess = "startProcess";
        public const string IntroComplete = "introComplete";
        public const string AssistantResponseGenerated = "assistantResponseGenerated";
        public const string Exit = "exit";
    }
}

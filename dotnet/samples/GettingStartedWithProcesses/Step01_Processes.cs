// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace GettingStartedWithProcesses;

/// <summary>
/// Demonstrate creation of <see cref="KernelProcess"/> and
/// eliciting its response to three explicit user messages.
/// </summary>
public class Step01_Processes(ITestOutputHelper output) : BaseTest(output)
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
        var userInputStep = process.AddStepFromType<UserInputStep>();
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
            .OnEvent(ChatBotEvents.UserInputReceived)
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
    private sealed class UserInputStep : KernelProcessStep<UserInputState>
    {
        /// <summary>
        /// The state object for the user input step. This object holds the user inputs and the current input index.
        /// </summary>
        private UserInputState? _state;

        /// <summary>
        /// Activates the user input step by initializing the state object. This method is called when the process is started
        /// and before any of the KernelFunctions are invoked.
        /// </summary>
        /// <param name="state">The state object for the step.</param>
        /// <returns>A <see cref="ValueTask"/></returns>
        public override ValueTask ActivateAsync(KernelProcessStepState<UserInputState> state)
        {
            state.State ??= new();
            _state = state.State;

            _state.UserInputs.Add("Hello");
            _state.UserInputs.Add("How are you?");
            _state.UserInputs.Add("exit");

            return ValueTask.CompletedTask;
        }

        /// <summary>
        /// Gets the user input.
        /// </summary>
        /// <param name="context">An instance of <see cref="KernelProcessStepContext"/> which can be
        /// used to emit events from within a KernelFunction.</param>
        /// <returns>A <see cref="ValueTask"/></returns>
        [KernelFunction("GetUserInput")]
        public async ValueTask GetUserInputAsync(KernelProcessStepContext context)
        {
            var input = _state!.UserInputs[_state.CurrentInputIndex];
            _state.CurrentInputIndex++;

            if (input.Equals("exit", StringComparison.OrdinalIgnoreCase))
            {
                // Emit the exit event
                await context.EmitEventAsync(new() { Id = ChatBotEvents.Exit });
                return;
            }

            // Emit the user input
            await context.EmitEventAsync(new() { Id = ChatBotEvents.UserInputReceived, Data = input });
        }
    }

    /// <summary>
    /// A step that takes the user input from a previous step and generates a response from the chat completion service.
    /// </summary>
    private sealed class ChatBotResponseStep : KernelProcessStep<ChatBotState>
    {
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
        [KernelFunction("GetChatResponse")]
        public async Task GetChatResponseAsync(KernelProcessStepContext context, string userMessage, Kernel _kernel)
        {
            _state!.ChatMessages.Add(new(AuthorRole.User, userMessage));
            IChatCompletionService chatService = _kernel.Services.GetRequiredService<IChatCompletionService>();
            ChatMessageContent response = await chatService.GetChatMessageContentAsync(_state.ChatMessages).ConfigureAwait(false);
            if (response != null)
            {
                _state.ChatMessages.Add(response!);
            }

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
    /// The state object for the <see cref="UserInputStep"/>
    /// </summary>
    private sealed record UserInputState
    {
        public List<string> UserInputs { get; init; } = new();

        public int CurrentInputIndex { get; set; } = 0;
    }

    /// <summary>
    /// A class that defines the events that can be emitted by the chat bot process. This is
    /// not required but used to ensure that the event names are consistent.
    /// </summary>
    private static class ChatBotEvents
    {
        public const string StartProcess = "startProcess";
        public const string IntroComplete = "introComplete";
        public const string UserInputReceived = "userInputReceived";
        public const string AssistantResponseGenerated = "assistantResponseGenerated";
        public const string Exit = "exit";
    }
}

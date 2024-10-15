// Copyright (c) Microsoft. All rights reserved.
using Events;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.History;
using Microsoft.SemanticKernel.ChatCompletion;
using SharedSteps;
using Step04.Steps;

namespace Step04;

/// <summary>
/// Demonstrate creation of a <see cref="KernelProcess"/> that orchestrates an <see cref="Agent"/> conversation.
/// For visual reference of the process check <see href="https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#step04_agentorchestration" >diagram</see>.
/// </summary>
public class Step04_AgentOrchestration(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
{
    // Target Open AI Services
    protected override bool ForceOpenAI => true;

    /// <summary>
    /// Orchestrates a single agent gathering user input and then delegating to a group of agents.
    /// The group of agents provide a response back to the single agent who continues to
    /// interact with the user.
    /// </summary>
    [Fact]
    public async Task DelegatedGroupChatAsync()
    {
        // Define process
        KernelProcess process = SetupAgentProcess<BasicAgentChatUserInput>(nameof(DelegatedGroupChatAsync));

        // Execute process
        await RunProcessAsync(process);
    }

    private sealed class BasicAgentChatUserInput : ScriptedUserInputStep
    {
        public BasicAgentChatUserInput()
        {
            this.SuppressOutput = true;
        }

        public override void PopulateUserInputs(UserInputState state)
        {
            state.UserInputs.Add("Hi");
            state.UserInputs.Add("I like green");
            state.UserInputs.Add("What is my favorite color?");
            state.UserInputs.Add("That's all, thank you");
        }
    }

    private async Task RunProcessAsync(KernelProcess process)
    {
        // Initialize services
        ChatHistory history = [];
        Kernel kernel = SetupKernel(history);

        // Execute process
        using LocalKernelProcessContext localProcess =
            await process.StartAsync(
                kernel,
                new KernelProcessEvent()
                {
                    Id = AgentOrchestrationEvents.StartProcess
                });

        // Demonstrate history is maintained independent of process state
        this.WriteHorizontalRule();
        foreach (ChatMessageContent message in history)
        {
            RenderMessageStep.Render(message);
        }
    }

    private KernelProcess SetupAgentProcess<TUserInputStep>(string processName) where TUserInputStep : ScriptedUserInputStep
    {
        ProcessBuilder process = new(processName);

        var userInputStep = process.AddStepFromType<TUserInputStep>();
        var renderMessageStep = process.AddStepFromType<RenderMessageStep>();
        var managerAgentStep = process.AddStepFromType<ManagerAgentStep>();
        var agentGroupStep = process.AddStepFromType<AgentGroupChatStep>();

        AttachErrorStep(
            userInputStep,
            ScriptedUserInputStep.Functions.GetUserInput);

        AttachErrorStep(
            managerAgentStep,
            ManagerAgentStep.Functions.InvokeAgent,
            ManagerAgentStep.Functions.InvokeGroup);

        AttachErrorStep(
            agentGroupStep,
            AgentGroupChatStep.Functions.InvokeAgentGroup);

        // Entry point
        process.OnInputEvent(AgentOrchestrationEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(userInputStep));

        // Pass user input to primary agent
        userInputStep
            .OnEvent(CommonEvents.UserInputReceived)
            .SendEventTo(new ProcessFunctionTargetBuilder(managerAgentStep, ManagerAgentStep.Functions.InvokeAgent))
            .SendEventTo(new ProcessFunctionTargetBuilder(renderMessageStep, RenderMessageStep.Functions.RenderUserText, parameterName: "message"));

        // Process completed
        userInputStep
            .OnEvent(CommonEvents.UserInputComplete)
            .SendEventTo(new ProcessFunctionTargetBuilder(renderMessageStep, RenderMessageStep.Functions.RenderDone))
            .StopProcess();

        // Render response from primary agent
        managerAgentStep
            .OnEvent(AgentOrchestrationEvents.AgentResponse)
            .SendEventTo(new ProcessFunctionTargetBuilder(renderMessageStep, RenderMessageStep.Functions.RenderMessage, parameterName: "message"));

        // Request more user input
        managerAgentStep
            .OnEvent(AgentOrchestrationEvents.AgentResponded)
            .SendEventTo(new ProcessFunctionTargetBuilder(userInputStep));

        // Delegate to inner agents
        managerAgentStep
            .OnEvent(AgentOrchestrationEvents.AgentWorking)
            .SendEventTo(new ProcessFunctionTargetBuilder(managerAgentStep, ManagerAgentStep.Functions.InvokeGroup));

        // Provide input to inner agents
        managerAgentStep
            .OnEvent(AgentOrchestrationEvents.GroupInput)
            .SendEventTo(new ProcessFunctionTargetBuilder(agentGroupStep, parameterName: "input"));

        // Render response from inner chat (for visibIlity)
        agentGroupStep
            .OnEvent(AgentOrchestrationEvents.GroupMessage)
            .SendEventTo(new ProcessFunctionTargetBuilder(renderMessageStep, RenderMessageStep.Functions.RenderInnerMessage, parameterName: "message"));

        // Provide inner response to primary agent
        agentGroupStep
            .OnEvent(AgentOrchestrationEvents.GroupCompleted)
            .SendEventTo(new ProcessFunctionTargetBuilder(managerAgentStep, ManagerAgentStep.Functions.ReceiveResponse, parameterName: "response"));

        KernelProcess kernelProcess = process.Build();

        return kernelProcess;

        void AttachErrorStep(ProcessStepBuilder step, params string[] functionNames)
        {
            foreach (string functionName in functionNames)
            {
                step
                    .OnFunctionError(functionName)
                    .SendEventTo(new ProcessFunctionTargetBuilder(renderMessageStep, RenderMessageStep.Functions.RenderError, "exception"))
                    .StopProcess();
            }
        }
    }

    private Kernel SetupKernel(ChatHistory history)
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        // Add Chat Completion to Kernel
        this.AddChatCompletionToKernel(builder);

        // Inject agents into service collection
        SetupAgents(builder, builder.Build());
        // Inject history provider into service collection
        builder.Services.AddSingleton<IChatHistoryProvider>(new ChatHistoryProvider(history));

        // NOTE: Uncomment to see process logging
        //builder.Services.AddSingleton<ILoggerFactory>(this.LoggerFactory);

        return builder.Build();
    }

    private const string ManagerInstructions =
        """
        Gather information from user until they have completely expressed their request.
        """;

    private const string FirstWorkerInstructions = // %%% INSTRUCTIONS
        """
        Complain
        """;

    private const string SecondWorkerInstructions = // %%% INSTRUCTIONS
        """
        Agree
        """;

    private static void SetupAgents(IKernelBuilder builder, Kernel kernel)
    {
        builder.Services.AddKeyedSingleton(ManagerAgentStep.AgentServiceKey, CreateAgent("Manager", ManagerInstructions, kernel.Clone()));
        SetupGroupChat(builder, kernel);
        builder.Services.AddKeyedSingleton(ManagerAgentStep.ReducerServiceKey, SetupReducer(kernel));
        builder.Services.AddKeyedSingleton(AgentGroupChatStep.ReducerServiceKey, SetupReducer(kernel));
    }

    private static ChatHistorySummarizationReducer SetupReducer(Kernel kernel) =>
         new(kernel.GetRequiredService<IChatCompletionService>(), 1); // %%% INSTRUCTIONS

    private static void SetupGroupChat(IKernelBuilder builder, Kernel kernel)
    {
        ChatCompletionAgent agent1 = CreateAgent("First", FirstWorkerInstructions, kernel.Clone());
        ChatCompletionAgent agent2 = CreateAgent("Second", SecondWorkerInstructions, kernel.Clone());
        AgentGroupChat chat =
            new(agent1, agent2)
            {
                // NOTE: Replace logger when using outside of sample.
                // Use `this.LoggerFactory` to observe logging output as part of sample.
                LoggerFactory = NullLoggerFactory.Instance,
                ExecutionSettings = new()
                {
                    SelectionStrategy =
                    {
                        //InitialAgent = agent1, // %%% BUG
                    },
                    TerminationStrategy =
                    {
                        MaximumIterations = 4,
                    }
                }
            };
        builder.Services.AddSingleton(chat);
    }

    private static ChatCompletionAgent CreateAgent(string name, string instructions, Kernel kernel) =>
        new()
        {
            Name = name,
            Instructions = instructions,
            Kernel = kernel.Clone(),
        };
}

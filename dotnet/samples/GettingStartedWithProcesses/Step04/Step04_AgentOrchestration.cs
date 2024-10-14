// Copyright (c) Microsoft. All rights reserved.

using Events;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using SharedSteps;
using Step04.Models;
using Step04.Steps;

namespace Step04;

/// <summary>
/// Demonstrate creation of a <see cref="KernelProcess"/> that orchestrates an <see cref="Agent"/> conversation.<br/>
/// For visual reference of the process check the <see href="https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#step04_agentorchestration" >diagram</see> . %%% TBD
/// </summary>
public class Step04_AgentOrchestration(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
{
    // Target Open AI Services
    protected override bool ForceOpenAI => true;

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    [Fact]
    public async Task CoordinateMultipleAgentsAsync()
    {
        await RunProcessAsync<UserInputTBD>(nameof(CoordinateMultipleAgentsAsync));
    }

    private sealed class UserInputTBD : ScriptedUserInputStep // %%% NAME
    {
        public UserInputTBD()
        {
            this.SuppressOutput = true;
        }

        public override void PopulateUserInputs(UserInputState state)
        {
            state.UserInputs.Add("Hi");
            state.UserInputs.Add("I like green");
            state.UserInputs.Add("What is my favorite color?");
        }
    }

    private async Task RunProcessAsync<TUserInputStep>(string processName) where TUserInputStep : ScriptedUserInputStep
    {
        // Initialize services
        ChatHistory history = [];
        Kernel kernel = SetupKernel(history);

        // Define process
        KernelProcess kernelProcess = SetupAgentProcess<TUserInputStep>(processName);

        // Execute process
        using LocalKernelProcessContext localProcess =
            await kernelProcess.StartAsync(
                kernel,
                new KernelProcessEvent()
                {
                    Id = AgentOrchestrationEvents.StartProcess
                });

        // Display history
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
        var workerAgentStep = process.AddStepFromType<WorkerAgentStep>();

        process.OnInputEvent(AgentOrchestrationEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(userInputStep));

        userInputStep
            .OnEvent(CommonEvents.UserInputReceived)
            .SendEventTo(new ProcessFunctionTargetBuilder(managerAgentStep, ManagerAgentStep.Functions.InvokeAgent))
            .SendEventTo(new ProcessFunctionTargetBuilder(renderMessageStep, RenderMessageStep.Functions.RenderUserText, "message"));

        userInputStep
            .OnEvent(AgentOrchestrationEvents.UserDone)
            .StopProcess();

        managerAgentStep
            .OnEvent(AgentOrchestrationEvents.AgentResponded)
            .SendEventTo(new ProcessFunctionTargetBuilder(userInputStep))
            .SendEventTo(new ProcessFunctionTargetBuilder(renderMessageStep, RenderMessageStep.Functions.RenderMessages, "messages"));

        managerAgentStep
            .OnEvent(AgentOrchestrationEvents.ManagerAgentWorking)
            .SendEventTo(new ProcessFunctionTargetBuilder(workerAgentStep))
            .SendEventTo(new ProcessFunctionTargetBuilder(renderMessageStep, RenderMessageStep.Functions.RenderMessages, "messages"));

        workerAgentStep
            .OnEvent(AgentOrchestrationEvents.AgentResponded)
            .SendEventTo(new ProcessFunctionTargetBuilder(managerAgentStep, ManagerAgentStep.Functions.ProcessResponse));

        process
            .OnInputEvent(WorkerAgentStep.Functions.InvokeAgent + ".Error")
            .SendEventTo(new ProcessFunctionTargetBuilder(renderMessageStep, RenderMessageStep.Functions.RenderError, "message"))
            .SendEventTo(new ProcessFunctionTargetBuilder(userInputStep));

        KernelProcess kernelProcess = process.Build();

        return kernelProcess;
    }

    private Kernel SetupKernel(ChatHistory history)
    {
        IKernelBuilder builder = Kernel.CreateBuilder();

        // Add Chat Completion to Kernel
        this.AddChatCompletionToKernel(builder);

        // Inject agents into service colletion
        SetupAgents(builder, builder.Build());

        // Inject history provider into service collection
        builder.Services.AddSingleton(new ChatHistoryProvider(history));

        return builder.Build();
    }

    private void SetupAgents(IKernelBuilder builder, Kernel kernel)
    {
        builder.Services.AddKeyedSingleton(ManagerAgentStep.AgentServiceKey, CreateAgent("Manager", "%% TBD", kernel.Clone()));
        builder.Services.AddKeyedSingleton(WorkerAgentStep.AgentServiceKey, CreateAgent("Worker", "%% TBD", kernel.Clone()));
    }

    private ChatCompletionAgent CreateAgent(string name, string instructions, Kernel kernel)
    {
        return
            new ChatCompletionAgent()
            {
                Name = name,
                Instructions = instructions,
                Kernel = kernel.Clone(),
            };
    }
}

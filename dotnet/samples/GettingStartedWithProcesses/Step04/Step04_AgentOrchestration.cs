// Copyright (c) Microsoft. All rights reserved.

using Events;
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
        //ChatHistory history = [];
        Kernel kernel = CreateKernelWithChatCompletion();
        KernelProcess kernelProcess = SetupAgentProcess<TUserInputStep>(processName);
        using LocalKernelProcessContext localProcess =
            await kernelProcess.StartAsync(
                kernel,
                new KernelProcessEvent()
                {
                    Id = AgentOrchestrationEvents.StartProcess,
                    //Data = history
                });

        this.WriteHorizontalRule();
        KernelProcessStepState state = kernelProcess.Steps.Where(info => info.InnerStepType == typeof(ManagerAgentStep)).Single().State; // $$$ STATE ???
        ChatHistory? history = ((KernelProcessStepState<ChatHistory>)state).State;
        if (history == null)
        {
            Console.WriteLine("NO AVAILABLE HISTORY");
        }
        else
        {
            foreach (ChatMessageContent message in history)
            {
                RenderMessageStep.Render(message);
            }
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

        managerAgentStep.OnEvent(AgentOrchestrationEvents.ManagerAgentResponded)
            .SendEventTo(new ProcessFunctionTargetBuilder(userInputStep))
            .SendEventTo(new ProcessFunctionTargetBuilder(renderMessageStep, RenderMessageStep.Functions.RenderMessages, "messages"));

        managerAgentStep
            .OnEvent(AgentOrchestrationEvents.ManagerAgentWorking)
            .SendEventTo(new ProcessFunctionTargetBuilder(workerAgentStep))
            .SendEventTo(new ProcessFunctionTargetBuilder(renderMessageStep, RenderMessageStep.Functions.RenderMessages, "messages"));

        workerAgentStep
            .OnEvent(AgentOrchestrationEvents.WorkerAgentResponded)
            .SendEventTo(new ProcessFunctionTargetBuilder(managerAgentStep, ManagerAgentStep.Functions.ProcessResponse));

        process
            .OnInputEvent(WorkerAgentStep.Functions.InvokeAgent + ".Error")
            .SendEventTo(new ProcessFunctionTargetBuilder(renderMessageStep, RenderMessageStep.Functions.RenderError, "message"))
            .SendEventTo(new ProcessFunctionTargetBuilder(userInputStep));
            //.StopProcess();

        KernelProcess kernelProcess = process.Build();

        return kernelProcess;
    }
}

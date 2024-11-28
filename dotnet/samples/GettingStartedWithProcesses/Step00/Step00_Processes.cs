// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step00.Steps;

namespace Step00;

/// <summary>
/// Demonstrate creation of the simplest <see cref="KernelProcess"/> and
/// eliciting its response to three explicit user messages.
/// </summary>
public class Step00_Processes(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
{
    public static class ProcessEvents
    {
        public const string StartProcess = nameof(StartProcess);
    }

    /// <summary>
    /// Demonstrates the creation of the simplest possible process with multiple steps
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task UseSimplestProcessAsync()
    {
        // Create a simple kernel 
        Kernel kernel = Kernel.CreateBuilder()
            .Build();

        ProcessBuilder processBuilder = new(nameof(Step00_Processes));

        // Create a process that will interact with the chat completion service
        ProcessBuilder process = new("ChatBot");
        var startStep = processBuilder.AddStepFromType<StartStep>();
        var doSomeWorkStep = processBuilder.AddStepFromType<DoSomeWorkStep>();
        var doMoreWorkStep = processBuilder.AddStepFromType<DoMoreWorkStep>();
        var lastStep = processBuilder.AddStepFromType<LastStep>();

        // Define the process flow
        processBuilder
            .OnInputEvent(ProcessEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(startStep));

        startStep
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(doSomeWorkStep));

        doSomeWorkStep
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(doMoreWorkStep));

        doMoreWorkStep
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(lastStep));

        lastStep
            .OnFunctionResult()
            .StopProcess();

        // Build the process to get a handle that can be started
        KernelProcess kernelProcess = process.Build();

        // Start the process with an initial external event
        using var runningProcess = await kernelProcess.StartAsync(
            kernel,
                new KernelProcessEvent()
                {
                    Id = ProcessEvents.StartProcess,
                    Data = null
                });
    }
}

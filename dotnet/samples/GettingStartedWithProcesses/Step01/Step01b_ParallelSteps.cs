// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process.Tools;
using Utilities;

namespace Step01;

/// <summary>
/// Demonstrate creation of <see cref="KernelProcess"/> and
/// eliciting its response to three explicit user messages.
/// </summary>
public class Step01b_ParallelSteps(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
{
    /// <summary>
    /// Demonstrates the creation of a simple process that has multiple steps, takes
    /// user input, interacts with the chat completion service, and demonstrates cycles
    /// in the process.
    /// </summary>
    /// <returns>A <see cref="Task"/></returns>
    [Fact]
    public async Task UseParallelProcessAsync()
    {
        // Create a kernel with a chat completion service
        Kernel kernel = Kernel.CreateBuilder()
            .AddOpenAIChatCompletion(
                modelId: TestConfiguration.OpenAI.ChatModelId,
                apiKey: TestConfiguration.OpenAI.ApiKey)
            .Build();

        // Create a process that will interact with the chat completion service
        ProcessBuilder process = new("Parallel");
        var rootStep = process.AddStepFromType<Root>();
        var aStep = process.AddStepFromType<StepA>();
        var bStep = process.AddStepFromType<StepB>();
        var finalStep = process.AddStepFromType<Final>();

        // Define the behavior when the process receives an external event
        process
            .OnInputEvent(ParallelEvents.StartProcess)
            .SendEventTo(new ProcessFunctionTargetBuilder(rootStep));

        // When the intro is complete, notify the userInput step
        rootStep
            .OnFunctionResult()
            .SendEventTo(new ProcessFunctionTargetBuilder(aStep))
            .SendEventTo(new ProcessFunctionTargetBuilder(bStep));

        aStep
            .OnEvent(ParallelEvents.NextStep)
            .SendEventTo(new ProcessFunctionTargetBuilder(finalStep, "Coalesce", "valueA"));

        bStep
            .OnEvent(ParallelEvents.NextStep)
            .SendEventTo(new ProcessFunctionTargetBuilder(finalStep, "Coalesce", "valueB"));

        finalStep
            .OnFunctionResult()
            .StopProcess();

        // Build the process to get a handle that can be started
        KernelProcess kernelProcess = process.Build();

        // Generate a Mermaid diagram for the process and print it to the console
        string mermaidGraph = kernelProcess.ToMermaid();
        Console.WriteLine($"=== Start - Mermaid Diagram for '{process.Name}' ===");
        Console.WriteLine(mermaidGraph);
        Console.WriteLine($"=== End - Mermaid Diagram for '{process.Name}' ===");

        // Generate an image from the Mermaid diagram
        string generatedImagePath = await MermaidRenderer.GenerateMermaidImageAsync(mermaidGraph, "ParallelProcess.png");
        Console.WriteLine($"Diagram generated at: {generatedImagePath}");

        // Start the process with an initial external event
        Console.WriteLine($"=== Start - Executing '{process.Name}' ===");
        //using var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent() { Id = ParallelEvents.StartProcess, Data = null });
        var runtime = new Microsoft.AutoGen.Core.InProcessRuntime();
        await runtime.StartAsync();
        using var runningProcess = await kernelProcess.StartAsync(kernel, runtime, new KernelProcessEvent() { Id = ParallelEvents.StartProcess, Data = null });
        await runtime.StopAsync();
        Console.WriteLine($"=== End - Executing '{process.Name}' ===");
    }

    /// <summary>
    /// %%%
    /// </summary>
    private sealed class Root : KernelProcessStep
    {
        /// <summary>
        /// Prints an introduction message to the console.
        /// </summary>
        [KernelFunction]
        public void SeedProcess()
        {
            System.Console.WriteLine($"EXECUTING STEP: {this.GetType().Name}");
        }
    }

    /// <summary>
    /// %%%
    /// </summary>
    private sealed class StepA : KernelProcessStep
    {
        /// <summary>
        /// Prints an introduction message to the console.
        /// </summary>
        [KernelFunction]
        public async Task ComputeAsync(KernelProcessStepContext context)
        {
            System.Console.WriteLine($"EXECUTING STEP: {this.GetType().Name}");
            await context.EmitEventAsync(new KernelProcessEvent { Id = ParallelEvents.NextStep, Data = 3 });
        }
    }

    /// <summary>
    /// %%%
    /// </summary>
    private sealed class StepB : KernelProcessStep
    {
        /// <summary>
        /// Prints an introduction message to the console.
        /// </summary>
        [KernelFunction]
        public async Task ComputeAsync(KernelProcessStepContext context)
        {
            System.Console.WriteLine($"EXECUTING STEP: {this.GetType().Name}");
            await context.EmitEventAsync(new KernelProcessEvent { Id = ParallelEvents.NextStep, Data = 8 });
        }
    }

    /// <summary>
    /// %%%
    /// </summary>
    private sealed class Final : KernelProcessStep
    {
        /// <summary>
        /// Prints an introduction message to the console.
        /// </summary>
        [KernelFunction]
        public void Coalesce(int valueA, int valueB)
        {
            System.Console.WriteLine($"EXECUTING STEP: {this.GetType().Name} [{valueA} + {valueB} = {valueA + valueB}]");
        }
    }

    /// <summary>
    /// A class that defines the events that can be emitted by the chat bot process. This is
    /// not required but used to ensure that the event names are consistent.
    /// </summary>
    private static class ParallelEvents
    {
        public const string StartProcess = "start";
        public const string NextStep = "next";
        public const string Exit = "exit";
    }
}

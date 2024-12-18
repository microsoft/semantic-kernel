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

        processBuilder
            .StartWith<StartStep>(ProcessEvents.StartProcess)
            .AndThen<DoSomeWorkStep>()
            .AndThen<DoMoreWorkStep>()
            .AndFinally<LastStep>();

        // Build the process to get a handle that can be started
        KernelProcess kernelProcess = processBuilder.Build();

        // Start the process with an initial external event
        using var runningProcess = await kernelProcess!.StartAsync(
            kernel,
                new KernelProcessEvent()
                {
                    Id = ProcessEvents.StartProcess,
                    Data = null
                });
    }
}

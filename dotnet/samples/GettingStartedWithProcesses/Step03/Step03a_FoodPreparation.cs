// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step03.Processes;

namespace Step03;

/// <summary>
/// Demonstrate creation of <see cref="KernelProcess"/> and
/// eliciting different food related events.
/// For visual reference of the processes used here check the diagram in: https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#step03a_foodPreparation
/// </summary>
public class Step03a_FoodPreparation(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
{
    // Target Open AI Services
    protected override bool ForceOpenAI => true;

    #region Stateless Processes
    [Fact]
    public async Task UsePrepareFriedFishProcessAsync()
    {
        var process = FriedFishProcess.CreateProcess();
        await UsePrepareSpecificProductAsync(process, FriedFishProcess.ProcessEvents.PrepareFriedFish);
    }

    [Fact]
    public async Task UsePreparePotatoFriesProcessAsync()
    {
        var process = PotatoFriesProcess.CreateProcess();
        await UsePrepareSpecificProductAsync(process, PotatoFriesProcess.ProcessEvents.PreparePotatoFries);
    }

    [Fact]
    public async Task UsePrepareFishSandwichProcessAsync()
    {
        var process = FishSandwichProcess.CreateProcess();
        await UsePrepareSpecificProductAsync(process, FishSandwichProcess.ProcessEvents.PrepareFishSandwich);
    }

    [Fact]
    public async Task UsePrepareFishAndChipsProcessAsync()
    {
        var process = FishAndChipsProcess.CreateProcess();
        await UsePrepareSpecificProductAsync(process, FishAndChipsProcess.ProcessEvents.PrepareFishAndChips);
    }
    #endregion
    #region Stateful Processes
    /// <summary>
    /// Test case that showcase when the same process is build multiple times, it will have different initial states
    /// </summary>
    /// <returns></returns>
    [Fact]
    public async Task UsePrepareStatefulFriedFishProcessNoSharedStateAsync()
    {
        var processBuilder = FriedFishProcess.CreateProcessWithStatefulSteps();
        var externalTriggerEvent = FriedFishProcess.ProcessEvents.PrepareFriedFish;

        Kernel kernel = CreateKernelWithChatCompletion();

        // Assert
        Console.WriteLine($"=== Start SK Process '{processBuilder.Name}' ===");
        await ExecuteProcessWithStateAsync(processBuilder.Build(), kernel, externalTriggerEvent, "Order 1");
        await ExecuteProcessWithStateAsync(processBuilder.Build(), kernel, externalTriggerEvent, "Order 2");
        Console.WriteLine($"=== End SK Process '{processBuilder.Name}' ===");
    }

    /// <summary>
    /// Test case that showcase when the same process is build once and used multiple times, it will have share the state
    /// and the state of the steps will become the initial state of the next running process
    /// </summary>
    /// <returns></returns>
    [Fact]
    public async Task UsePrepareStatefulFriedFishProcessSharedStateAsync()
    {
        var processBuilder = FriedFishProcess.CreateProcessWithStatefulSteps();
        var externalTriggerEvent = FriedFishProcess.ProcessEvents.PrepareFriedFish;

        Kernel kernel = CreateKernelWithChatCompletion();
        KernelProcess kernelProcess = processBuilder.Build();

        Console.WriteLine($"=== Start SK Process '{processBuilder.Name}' ===");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, externalTriggerEvent, "Order 1");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, externalTriggerEvent, "Order 2");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, externalTriggerEvent, "Order 3");
        Console.WriteLine($"=== End SK Process '{processBuilder.Name}' ===");
    }

    [Fact]
    public async Task UsePrepareStatefulPotatoFriesProcessSharedStateAsync()
    {
        var processBuilder = PotatoFriesProcess.CreateProcessWithStatefulSteps();
        var externalTriggerEvent = PotatoFriesProcess.ProcessEvents.PreparePotatoFries;

        Kernel kernel = CreateKernelWithChatCompletion();
        KernelProcess kernelProcess = processBuilder.Build();

        Console.WriteLine($"=== Start SK Process '{processBuilder.Name}' ===");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, externalTriggerEvent, "Order 1");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, externalTriggerEvent, "Order 2");
        await ExecuteProcessWithStateAsync(kernelProcess, kernel, externalTriggerEvent, "Order 3");
        Console.WriteLine($"=== End SK Process '{processBuilder.Name}' ===");
    }

    private async Task<KernelProcess> ExecuteProcessWithStateAsync(KernelProcess process, Kernel kernel, string externalTriggerEvent, string orderLabel)
    {
        Console.WriteLine($"=== {orderLabel} ===");
        var runningProcess = await process.StartAsync(kernel, new KernelProcessEvent()
        {
            Id = externalTriggerEvent,
            Data = new List<string>()
        });
        return await runningProcess.GetStateAsync();
    }
    #endregion
    protected async Task UsePrepareSpecificProductAsync(ProcessBuilder processBuilder, string externalTriggerEvent)
    {
        // Arrange
        Kernel kernel = CreateKernelWithChatCompletion();

        // Act
        KernelProcess kernelProcess = processBuilder.Build();

        // Assert
        Console.WriteLine($"=== Start SK Process '{processBuilder.Name}' ===");
        using var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent()
        {
            Id = externalTriggerEvent, Data = new List<string>()
        });
        Console.WriteLine($"=== End SK Process '{processBuilder.Name}' ===");
    }
}

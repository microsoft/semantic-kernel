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

    protected async Task UsePrepareSpecificProductAsync(ProcessBuilder processBuilder, string externalTriggerEvent)
    {
        // Arrange
        Kernel kernel = CreateKernelWithChatCompletion();

        // Act
        KernelProcess kernelProcess = processBuilder.Build();

        // Assert
        using var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent()
        {
            Id = externalTriggerEvent, Data = new List<string>()
        });
    }
}

// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step03.Models;
using Step03.Processes;

namespace Step03;

/// <summary>
/// Demonstrate creation of <see cref="KernelProcess"/> and
/// eliciting its response to three explicit user messages.
/// For visual reference of the processes used here check the diagram in: https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#step03_foodPreparation
/// </summary>
public class Step03_FoodPreparation(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
{
    [Fact]
    public async Task UsePrepareFriedFishProcessAsync()
    {
        var process = new PrepareFriedFishProcess();
        await UsePrepareSpecificProductAsync(process.GetProcess(), process.GetExternalInputTriggerEvents());
    }

    [Fact]
    public async Task UsePreparePotatoFriesProcessAsync()
    {
        var process = new PreparePotatoFriesProcess();
        await UsePrepareSpecificProductAsync(process.GetProcess(), process.GetExternalInputTriggerEvents());
    }

    [Fact]
    public async Task UsePrepareFishSandwichProcessAsync()
    {
        var process = new PrepareFishSandwichProcess();
        await UsePrepareSpecificProductAsync(process.GetProcess(), process.GetExternalInputTriggerEvents());
    }

    [Fact]
    public async Task UsePrepareFishAndChipsProcessAsync()
    {
        var process = new PrepareFishAndChipsProcess();
        await UsePrepareSpecificProductAsync(process.GetProcess(), process.GetExternalInputTriggerEvents());
    }

    protected async Task UsePrepareSpecificProductAsync(ProcessBuilder processBuilder, List<string> externalTriggerEvents)
    {
        // Arrange
        Kernel kernel = CreateKernelWithChatCompletion();

        // Act
        KernelProcess kernelProcess = processBuilder.Build();

        // Assert
        Assert.Single(externalTriggerEvents);
        var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent()
        {
            Id = externalTriggerEvents.First(),
        });
    }

    [Fact]
    public async Task UseSingleOrderFriedFishAsync()
    {
        await UsePrepareFoodOrderProcessSingleItemAsync(FoodItem.FriedFish);
    }

    [Fact]
    public async Task UseSingleOrderPotatoFriesAsync()
    {
        await UsePrepareFoodOrderProcessSingleItemAsync(FoodItem.PotatoFries);
    }

    [Fact]
    public async Task UseSingleOrderFishSandwichAsync()
    {
        await UsePrepareFoodOrderProcessSingleItemAsync(FoodItem.FishSandwich);
    }

    [Fact]
    public async Task UseSingleOrderFishAndChipsAsync()
    {
        await UsePrepareFoodOrderProcessSingleItemAsync(FoodItem.FishAndChips);
    }

    protected async Task UsePrepareFoodOrderProcessSingleItemAsync(FoodItem foodItem)
    {
        Kernel kernel = CreateKernelWithChatCompletion();
        var process = new PrepareSingleFoodItemProcess();
        KernelProcess kernelProcess = process.GetProcess().Build();

        var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent()
        {
            Id = process.GetExternalInputTriggerEvents().First(),
            Data = foodItem
        });
    }

    protected new Kernel CreateKernelWithChatCompletion()
    {
        var builder = Kernel.CreateBuilder();
        builder.AddOpenAIChatCompletion(
            TestConfiguration.OpenAI.ChatModelId,
            TestConfiguration.OpenAI.ApiKey);

        return builder.Build();
    }
}

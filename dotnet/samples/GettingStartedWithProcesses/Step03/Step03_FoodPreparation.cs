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
        Kernel kernel = Kernel.CreateBuilder().Build();

        var process = new PrepareFriedFishProcess();
        var kernelProcess = process.GetProcess().Build();

        var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent()
        {
            Id = process.GetExternalInputTriggerEvents().First(),
        });
    }

    [Fact]
    public async Task UsePreparePotatoFriesProcessAsync()
    {
        Kernel kernel = Kernel.CreateBuilder().Build();

        var process = new PreparePotatoFriesProcess();
        var kernelProcess = process.GetProcess().Build();

        var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent()
        {
            Id = process.GetExternalInputTriggerEvents().First(),
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

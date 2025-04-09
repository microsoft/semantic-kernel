// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Step03.Models;
using Step03.Processes;

namespace Step03;

/// <summary>
/// Demonstrate creation of <see cref="KernelProcess"/> and
/// eliciting different food related events.
/// For visual reference of the processes used here check the diagram in: https://github.com/microsoft/semantic-kernel/tree/main/dotnet/samples/GettingStartedWithProcesses/README.md#step03b_foodOrdering
/// </summary>
public class Step03b_FoodOrdering(ITestOutputHelper output) : BaseTest(output, redirectSystemConsoleOutput: true)
{
    // Target Open AI Services
    protected override bool ForceOpenAI => true;

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
        KernelProcess kernelProcess = SingleFoodItemProcess.CreateProcess().Build();

        await using var runningProcess = await kernelProcess.StartAsync(kernel, new KernelProcessEvent()
        {
            Id = SingleFoodItemProcess.ProcessEvents.SingleOrderReceived,
            Data = foodItem
        });
    }
}

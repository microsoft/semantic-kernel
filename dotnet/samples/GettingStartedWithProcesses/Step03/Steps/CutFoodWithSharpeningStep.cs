// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Process;

namespace Step03.Steps;

/// <summary>
/// Step used in the Processes Samples:
/// - Step_03_FoodPreparation.cs
/// </summary>
[KernelProcessStepMetadata("CutFoodStep.V2")]
public class CutFoodWithSharpeningStep : KernelProcessStep<CutFoodWithSharpeningState>
{
    public static class ProcessStepFunctions
    {
        public const string ChopFood = nameof(ChopFood);
        public const string SliceFood = nameof(SliceFood);
        public const string SharpenKnife = nameof(SharpenKnife);
    }

    public static class OutputEvents
    {
        public const string ChoppingReady = nameof(ChoppingReady);
        public const string SlicingReady = nameof(SlicingReady);
        public const string KnifeNeedsSharpening = nameof(KnifeNeedsSharpening);
        public const string KnifeSharpened = nameof(KnifeSharpened);
    }

    internal CutFoodWithSharpeningState? _state;

    public override ValueTask ActivateAsync(KernelProcessStepState<CutFoodWithSharpeningState> state)
    {
        _state = state.State;
        return ValueTask.CompletedTask;
    }

    [KernelFunction(ProcessStepFunctions.ChopFood)]
    public async Task ChopFoodAsync(KernelProcessStepContext context, List<string> foodActions)
    {
        var foodToBeCut = foodActions.First();
        if (this.KnifeNeedsSharpening())
        {
            Console.WriteLine($"CUTTING_STEP: Dull knife, cannot chop {foodToBeCut} - needs sharpening.");
            await context.EmitEventAsync(new() { Id = OutputEvents.KnifeNeedsSharpening, Data = foodActions });
            return;
        }
        // Update knife sharpness
        this._state!.KnifeSharpness--;

        // Chop food
        foodActions.Add(this.getActionString(foodToBeCut, "chopped"));
        Console.WriteLine($"CUTTING_STEP: Ingredient {foodToBeCut} has been chopped! - knife sharpness: {this._state.KnifeSharpness}");
        await context.EmitEventAsync(new() { Id = OutputEvents.ChoppingReady, Data = foodActions });
    }

    [KernelFunction(ProcessStepFunctions.SliceFood)]
    public async Task SliceFoodAsync(KernelProcessStepContext context, List<string> foodActions)
    {
        var foodToBeCut = foodActions.First();
        if (this.KnifeNeedsSharpening())
        {
            Console.WriteLine($"CUTTING_STEP: Dull knife, cannot slice {foodToBeCut} - needs sharpening.");
            await context.EmitEventAsync(new() { Id = OutputEvents.KnifeNeedsSharpening, Data = foodActions });
            return;
        }
        // Update knife sharpness
        this._state!.KnifeSharpness--;

        // Slice food
        foodActions.Add(this.getActionString(foodToBeCut, "sliced"));
        Console.WriteLine($"CUTTING_STEP: Ingredient {foodToBeCut} has been sliced! - knife sharpness: {this._state.KnifeSharpness}");
        await context.EmitEventAsync(new() { Id = OutputEvents.SlicingReady, Data = foodActions });
    }

    [KernelFunction(ProcessStepFunctions.SharpenKnife)]
    public async Task SharpenKnifeAsync(KernelProcessStepContext context, List<string> foodActions)
    {
        this._state!.KnifeSharpness += this._state._sharpeningBoost;
        Console.WriteLine($"KNIFE SHARPENED: Knife sharpness is now {this._state.KnifeSharpness}!");
        await context.EmitEventAsync(new() { Id = OutputEvents.KnifeSharpened, Data = foodActions });
    }

    private bool KnifeNeedsSharpening() => this._state?.KnifeSharpness == this._state?._needsSharpeningLimit;

    private string getActionString(string food, string action)
    {
        return $"{food}_{action}";
    }
}

/// <summary>
/// The state object for the <see cref="CutFoodWithSharpeningStep"/>.
/// </summary>
public sealed class CutFoodWithSharpeningState
{
    public int KnifeSharpness { get; set; } = 5;

    internal int _needsSharpeningLimit = 3;
    internal int _sharpeningBoost = 5;
}

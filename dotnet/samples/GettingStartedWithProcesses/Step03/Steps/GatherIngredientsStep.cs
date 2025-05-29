// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel;
using Step03.Models;
namespace Step03.Steps;

/// <summary>
/// Step used as base by many other cooking processes
/// When used in other processes a new step is based on this one with custom GatherIngredientsAsync functionality
/// </summary>
public class GatherIngredientsStep : KernelProcessStep
{
    public static class ProcessStepFunctions
    {
        public const string GatherIngredients = nameof(GatherIngredients);
    }

    public static class OutputEvents
    {
        public const string IngredientsGathered = nameof(IngredientsGathered);
    }

    private readonly FoodIngredients _ingredient;

    public GatherIngredientsStep(FoodIngredients ingredient)
    {
        this._ingredient = ingredient;
    }

    /// <summary>
    /// Method to be overridden by the user set custom ingredients to be gathered and events to be triggered
    /// </summary>
    /// <param name="context">The context for the current step and process. <see cref="KernelProcessStepContext"/></param>
    /// <param name="foodActions">list of actions taken to the food</param>
    /// <returns></returns>
    [KernelFunction(ProcessStepFunctions.GatherIngredients)]
    public virtual async Task GatherIngredientsAsync(KernelProcessStepContext context, List<string> foodActions)
    {
        var ingredient = this._ingredient.ToFriendlyString();
        var updatedFoodActions = new List<string>();
        updatedFoodActions.AddRange(foodActions);
        if (updatedFoodActions.Count == 0)
        {
            updatedFoodActions.Add(ingredient);
        }
        updatedFoodActions.Add($"{ingredient}_gathered");

        Console.WriteLine($"GATHER_INGREDIENT: Gathered ingredient {ingredient}");
        await context.EmitEventAsync(new() { Id = OutputEvents.IngredientsGathered, Data = updatedFoodActions });
    }
}

/// <summary>
/// Stateful Step used as base by many other cooking processes
/// When used in other processes a new step is based on this one with custom GatherIngredientsAsync functionality
/// </summary>
public class GatherIngredientsWithStockStep : KernelProcessStep<GatherIngredientsState>
{
    public static class ProcessStepFunctions
    {
        public const string GatherIngredients = nameof(GatherIngredients);
    }

    public static class OutputEvents
    {
        public const string IngredientsGathered = nameof(IngredientsGathered);
        public const string IngredientsOutOfStock = nameof(IngredientsOutOfStock);
    }

    private readonly FoodIngredients _ingredient;

    public GatherIngredientsWithStockStep(FoodIngredients ingredient)
    {
        this._ingredient = ingredient;
    }

    internal GatherIngredientsState? _state;

    public override ValueTask ActivateAsync(KernelProcessStepState<GatherIngredientsState> state)
    {
        _state = state.State;
        return ValueTask.CompletedTask;
    }

    /// <summary>
    /// Method to be overridden by the user set custom ingredients to be gathered and events to be triggered
    /// </summary>
    /// <param name="context">The context for the current step and process. <see cref="KernelProcessStepContext"/></param>
    /// <param name="foodActions">list of actions taken to the food</param>
    /// <returns></returns>
    [KernelFunction(ProcessStepFunctions.GatherIngredients)]
    public virtual async Task GatherIngredientsAsync(KernelProcessStepContext context, List<string> foodActions)
    {
        var ingredient = this._ingredient.ToFriendlyString(); ;
        var updatedFoodActions = new List<string>();
        updatedFoodActions.AddRange(foodActions);

        if (this._state!.IngredientsStock == 0)
        {
            Console.WriteLine($"GATHER_INGREDIENT: Could not gather {ingredient} - OUT OF STOCK!");
            await context.EmitEventAsync(new() { Id = OutputEvents.IngredientsOutOfStock, Data = updatedFoodActions });
            return;
        }

        if (updatedFoodActions.Count == 0)
        {
            updatedFoodActions.Add(ingredient);
        }
        updatedFoodActions.Add($"{ingredient}_gathered");

        // Updating stock of ingredients
        this._state.IngredientsStock--;

        Console.WriteLine($"GATHER_INGREDIENT: Gathered ingredient {ingredient} - remaining: {this._state.IngredientsStock}");
        await context.EmitEventAsync(new() { Id = OutputEvents.IngredientsGathered, Data = updatedFoodActions });
    }
}

/// <summary>
/// The state object for the <see cref="GatherIngredientsWithStockStep"/>.
/// </summary>
public sealed class GatherIngredientsState
{
    public int IngredientsStock { get; set; } = 5;
}

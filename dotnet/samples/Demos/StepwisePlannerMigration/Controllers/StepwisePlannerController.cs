// Copyright (c) Microsoft. All rights reserved.

using Microsoft.AspNetCore.Mvc;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Planning;
using StepwisePlannerMigration.Models;
using StepwisePlannerMigration.Plugins;
using StepwisePlannerMigration.Services;

namespace StepwisePlannerMigration.Controllers;

/// <summary>
/// This controller shows the old way how to use planning capability by using <see cref="FunctionCallingStepwisePlanner"/>.
/// A new recommended approach is demonstrated in <see cref="AutoFunctionCallingController"/>.
/// </summary>
[ApiController]
[Route("stepwise-planner")]
public class StepwisePlannerController : ControllerBase
{
    private readonly Kernel _kernel;
    private readonly FunctionCallingStepwisePlanner _planner;
    private readonly IPlanProvider _planProvider;

    public StepwisePlannerController(
        Kernel kernel,
        FunctionCallingStepwisePlanner planner,
        IPlanProvider planProvider)
    {
        this._kernel = kernel;
        this._planner = planner;
        this._planProvider = planProvider;

        this._kernel.ImportPluginFromType<TimePlugin>();
        this._kernel.ImportPluginFromType<WeatherPlugin>();
    }

    /// <summary>
    /// Action to generate a plan. Generated plan will be populated in <see cref="ChatHistory"/> object.
    /// </summary>
    [HttpPost, Route("generate-plan")]
    public async Task<IActionResult> GeneratePlanAsync(PlanRequest request)
    {
        FunctionCallingStepwisePlannerResult result = await this._planner.ExecuteAsync(this._kernel, request.Goal);

        return this.Ok(result.ChatHistory);
    }

    /// <summary>
    /// Action to execute a new plan.
    /// </summary>
    [HttpPost, Route("execute-new-plan")]
    public async Task<IActionResult> ExecuteNewPlanAsync(PlanRequest request)
    {
        FunctionCallingStepwisePlannerResult result = await this._planner.ExecuteAsync(this._kernel, request.Goal);

        return this.Ok(result.FinalAnswer);
    }

    /// <summary>
    /// Action to execute existing plan. Generated plans can be stored in permanent storage for reusability.
    /// In this demo application it is stored in file.
    /// </summary>
    [HttpPost, Route("execute-existing-plan")]
    public async Task<IActionResult> ExecuteExistingPlanAsync(PlanRequest request)
    {
        ChatHistory chatHistory = this._planProvider.GetPlan("stepwise-plan.json");
        FunctionCallingStepwisePlannerResult result = await this._planner.ExecuteAsync(this._kernel, request.Goal, chatHistory);

        return this.Ok(result.FinalAnswer);
    }
}

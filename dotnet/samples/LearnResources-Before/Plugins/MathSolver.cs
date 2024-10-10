// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Planning.Handlebars;

namespace Plugins;

public class MathSolver(ILoggerFactory loggerFactory)
{
    private readonly ILogger _logger = loggerFactory.CreateLogger<MathSolver>();

    [KernelFunction]
    [Description("Solves a math problem.")]
    [return: Description("The solution to the math problem.")]
    public async Task<string> SolveAsync(
        Kernel kernel,
        [Description("The math problem to solve; describe it in 2-3 sentences to ensure full context is provided")] string problem
    )
    {
        var kernelWithMath = kernel.Clone();

        // Remove the math solver plugin so that we don't get into an infinite loop
        kernelWithMath.Plugins.Remove(kernelWithMath.Plugins["MathSolver"]);

        // Add the math plugin so the LLM can solve the problem
        kernelWithMath.Plugins.AddFromType<MathPlugin>();

        var planner = new HandlebarsPlanner(new HandlebarsPlannerOptions() { AllowLoops = true });

        // Create a plan
        var plan = await planner.CreatePlanAsync(kernelWithMath, problem);
        this._logger.LogInformation("Plan: {Plan}", plan);

        // Execute the plan
        var result = (await plan.InvokeAsync(kernelWithMath)).Trim();
        this._logger.LogInformation("Results: {Result}", result);

        return result;
    }
}

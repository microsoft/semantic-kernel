// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.CoreSkills;

/// <summary>
/// <para>Semantic skill that creates and executes plans.</para>
/// <para>
/// Usage:
/// var kernel = SemanticKernel.Build(ConsoleLogger.Log);
/// kernel.ImportSkill("planner", new PlannerSkill(kernel));
/// </para>
/// </summary>
public class PlannerSkill
{
    /// <summary>
    /// Parameter names.
    /// <see cref="ContextVariables"/>
    /// </summary>
    public static class Parameters
    {
        /// <summary>
        /// The number of buckets to create
        /// </summary>
        public const string BucketCount = "bucketCount";

        /// <summary>
        /// The prefix to use for the bucket labels
        /// </summary>
        public const string BucketLabelPrefix = "bucketLabelPrefix";

        /// <summary>
        /// The relevancy threshold when filtering registered functions.
        /// </summary>
        public const string RelevancyThreshold = "relevancyThreshold";

        /// <summary>
        /// The maximum number of relevant functions as result of semantic search to include in the plan creation request.
        /// </summary>
        public const string MaxRelevantFunctions = "MaxRelevantFunctions";

        /// <summary>
        /// The list of skills to exclude from the plan creation request.
        /// </summary>
        public const string ExcludedSkills = "excludedSkills";

        /// <summary>
        /// The list of functions to exclude from the plan creation request.
        /// </summary>
        public const string ExcludedFunctions = "excludedFunctions";

        /// <summary>
        /// The list of functions to include in the plan creation request.
        /// </summary>
        public const string IncludedFunctions = "includedFunctions";

        /// <summary>
        /// Whether to use conditional capabilities when creating plans.
        /// </summary>
        public const string UseConditionals = "useConditionals";
    }

    internal sealed class PlannerSkillConfig
    {
        // Depending on the embeddings engine used, the user ask,
        // and the functions available, this value may need to be adjusted.
        // For default, this is set to null to exhibit previous behavior.
        public double? RelevancyThreshold { get; set; }

        // Limits the number of relevant functions as result of semantic
        // search included in the plan creation request.
        // <see cref="Parameters.IncludedFunctions"/> will be included
        // in the plan regardless of this limit.
        public int MaxRelevantFunctions { get; set; } = 100;

        // A list of skills to exclude from the plan creation request.
        public HashSet<string> ExcludedSkills { get; } = new() { RestrictedSkillName };

        // A list of functions to exclude from the plan creation request.
        public HashSet<string> ExcludedFunctions { get; } = new() { "CreatePlan", "ExecutePlan" };

        // A list of functions to include in the plan creation request.
        public HashSet<string> IncludedFunctions { get; } = new() { "BucketOutputs" };

        // Whether to use conditional capabilities when creating plans.
        public bool UseConditionals { get; set; } = false;
    }

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from the PlannerSkill plans
    /// </summary>
    private const string RestrictedSkillName = "PlannerSkill_Excluded";

    /// <summary>
    /// the function flow runner, which executes plans that leverage functions
    /// </summary>
    private readonly FunctionFlowRunner _functionFlowRunner;

    /// <summary>
    /// the bucket semantic function, which takes a list of items and buckets them into a number of buckets
    /// </summary>
    private readonly ISKFunction _bucketFunction;

    /// <summary>
    /// the function flow semantic function, which takes a goal and creates an xml plan that can be executed
    /// </summary>
    private readonly ISKFunction _functionFlowFunction;

    /// <summary>
    /// the conditional function flow semantic function, which takes a goal and creates an xml plan that can be executed
    /// </summary>
    private readonly ISKFunction _conditionalFunctionFlowFunction;

    /// <summary>
    /// Initializes a new instance of the <see cref="PlannerSkill"/> class.
    /// </summary>
    /// <param name="kernel"> The kernel to use </param>
    /// <param name="maxTokens"> The maximum number of tokens to use for the semantic functions </param>
    public PlannerSkill(IKernel kernel, int maxTokens = 1024)
    {
        this._functionFlowRunner = new(kernel);

        this._bucketFunction = kernel.CreateSemanticFunction(
            promptTemplate: SemanticFunctionConstants.BucketFunctionDefinition,
            skillName: RestrictedSkillName,
            maxTokens: maxTokens,
            temperature: 0.0);

        this._functionFlowFunction = kernel.CreateSemanticFunction(
            promptTemplate: SemanticFunctionConstants.FunctionFlowFunctionDefinition,
            skillName: RestrictedSkillName,
            description: "Given a request or command or goal generate a step by step plan to " +
                         "fulfill the request using functions. This ability is also known as decision making and function flow",
            maxTokens: maxTokens,
            temperature: 0.0,
            stopSequences: new[] { "<!--" });

        this._conditionalFunctionFlowFunction = kernel.CreateSemanticFunction(
            promptTemplate: SemanticFunctionConstants.ConditionalFunctionFlowFunctionDefinition,
            skillName: RestrictedSkillName,
            description: "Given a request or command or goal generate a step by step plan to " +
                         "fulfill the request using functions. This ability is also known as decision making and function flow. Uses conditional capabilities",
            maxTokens: maxTokens,
            temperature: 0.0,
            stopSequences: new[] { "<!--" });

        // Currently not exposed -- experimental.
        _ = kernel.CreateSemanticFunction(
            SemanticFunctionConstants.ProblemSolverFunctionDefinition,
            skillName: RestrictedSkillName,
            description: "Given a request or command or goal generate a step by step plan to fulfill the request. " +
                         "This ability is also known as decision making and problem solving",
            maxTokens: maxTokens,
            temperature: 0.0,
            stopSequences: new[] { "<!--" });

        _ = kernel.CreateSemanticFunction(
            SemanticFunctionConstants.SolveNextStepFunctionDefinition,
            skillName: RestrictedSkillName,
            description: "Given a plan with a goal, take the first step and execute it",
            maxTokens: maxTokens,
            temperature: 0.0,
            stopSequences: new[] { "<!-- END -->", "<!--" });
    }

    /// <summary>
    /// When the output of a function is too big, parse the output into a number of buckets.
    /// </summary>
    /// <param name="input"> The input from a function that needs to be parsed into buckets. </param>
    /// <param name="context"> The context to use </param>
    /// <returns> The context with the bucketed results </returns>
    [SKFunction("When the output of a function is too big, parse the output into a number of buckets.")]
    [SKFunctionName("BucketOutputs")]
    [SKFunctionInput(Description = "The output from a function that needs to be parse into buckets.")]
    [SKFunctionContextParameter(Name = Parameters.BucketCount, Description = "The number of buckets.", DefaultValue = "")]
    [SKFunctionContextParameter(
        Name = Parameters.BucketLabelPrefix,
        Description = "The target label prefix for the resulting buckets. " +
                      "Result will have index appended e.g. bucketLabelPrefix='Result' => Result_1, Result_2, Result_3",
        DefaultValue = "Result")]
    public async Task<SKContext> BucketOutputsAsync(string input, SKContext context)
    {
        var bucketsAdded = 0;

        var bucketVariables = new ContextVariables(input);
        if (context.Variables.Get(Parameters.BucketCount, out var bucketCount))
        {
            bucketVariables.Set(Parameters.BucketCount, bucketCount);
        }

        // {'buckets': ['Result 1\nThis is the first result.', 'Result 2\nThis is the second result. It's doubled!', 'Result 3\nThis is the third and final result. Truly astonishing.']}
        var result = await this._bucketFunction.InvokeAsync(new SKContext(bucketVariables, context.Memory, context.Skills, context.Log,
            context.CancellationToken));

        try
        {
            // May need additional formatting here.
            var resultString = result.Result
                .Replace("\\n", "\n")
                .Replace("\n", "\\n");

            var resultObject = JsonSerializer.Deserialize<Dictionary<string, List<string>>>(resultString);

            if (context.Variables.Get(Parameters.BucketLabelPrefix, out var bucketLabelPrefix) &&
                resultObject?.ContainsKey("buckets") == true)
            {
                foreach (var item in resultObject["buckets"])
                {
                    var bucketLabel = $"{bucketLabelPrefix}_{++bucketsAdded}";
                    context.Variables.Set($"{bucketLabel}", item);
                }
            }

            return context;
        }
        catch (Exception e) when (
            e is JsonException or
                InvalidCastException or
                NotSupportedException or
                ArgumentNullException)
        {
            context.Log.LogWarning("Error parsing bucket outputs: {0}", e.Message);
            return context.Fail($"Error parsing bucket outputs: {e.Message}");
        }
    }

    /// <summary>
    /// Create a plan using registered functions to accomplish a goal.
    /// </summary>
    /// <param name="goal"> The goal to accomplish. </param>
    /// <param name="context"> The context to use </param>
    /// <returns> The context with the plan </returns>
    /// <remarks>
    /// The plan is stored in the context as a string. The plan is also stored in the context as a Plan object.
    /// </remarks>
    [SKFunction("Create a plan using registered functions to accomplish a goal.")]
    [SKFunctionName("CreatePlan")]
    [SKFunctionInput(Description = "The goal to accomplish.")]
    [SKFunctionContextParameter(Name = Parameters.RelevancyThreshold, Description = "The relevancy threshold when filtering registered functions.",
        DefaultValue = "")]
    [SKFunctionContextParameter(Name = Parameters.MaxRelevantFunctions,
        Description = "Limits the number of relevant functions as result of semantic search included in the plan creation request.", DefaultValue = "100")]
    [SKFunctionContextParameter(Name = Parameters.ExcludedFunctions, Description = "A list of functions to exclude from the plan creation request.",
        DefaultValue = "")]
    [SKFunctionContextParameter(Name = Parameters.ExcludedSkills, Description = "A list of skills to exclude from the plan creation request.",
        DefaultValue = "")]
    [SKFunctionContextParameter(Name = Parameters.IncludedFunctions, Description = "A list of functions to include in the plan creation request.",
        DefaultValue = "")]
    [SKFunctionContextParameter(Name = Parameters.UseConditionals, Description = "Use conditional functions to create the plan.",
        DefaultValue = "False")]
    public async Task<SKContext> CreatePlanAsync(string goal, SKContext context)
    {
        PlannerSkillConfig config = context.GetPlannerSkillConfig();

        string relevantFunctionsManual = await context.GetFunctionsManualAsync(goal, config);
        context.Variables.Set("available_functions", relevantFunctionsManual);
        // TODO - consider adding the relevancy score for functions added to manual

        var plan = config.UseConditionals
            ? await this._conditionalFunctionFlowFunction.InvokeAsync(context)
            : await this._functionFlowFunction.InvokeAsync(context);

        string fullPlan = $"<{FunctionFlowRunner.GoalTag}>\n{goal}\n</{FunctionFlowRunner.GoalTag}>\n{plan.ToString().Trim()}";
        _ = context.Variables.UpdateWithPlanEntry(new SkillPlan
        {
            Id = Guid.NewGuid().ToString("N"),
            Goal = goal,
            PlanString = fullPlan,
        });

        return context;
    }

    /// <summary>
    /// Execute a plan that uses registered functions to accomplish a goal.
    /// </summary>
    /// <param name="context"> The context to use </param>
    /// <returns> The context with the plan </returns>
    /// <remarks>
    /// The plan is stored in the context as a string. The plan is also stored in the context as a Plan object.
    /// </remarks>
    [SKFunction("Execute a plan that uses registered functions to accomplish a goal.")]
    [SKFunctionName("ExecutePlan")]
    public async Task<SKContext> ExecutePlanAsync(SKContext context)
    {
        var planToExecute = context.Variables.ToPlan();
        try
        {
            var executeResultContext = await this._functionFlowRunner.ExecuteXmlPlanAsync(context, planToExecute.PlanString);
            _ = executeResultContext.Variables.Get(SkillPlan.PlanKey, out var planProgress);
            _ = executeResultContext.Variables.Get(SkillPlan.ResultKey, out var results);

            bool containsPlanTag = planProgress.IndexOf($"<{FunctionFlowRunner.PlanTag}>", StringComparison.OrdinalIgnoreCase) >= 0;
            var isComplete = containsPlanTag && planProgress.IndexOf($"<{FunctionFlowRunner.FunctionTag}", StringComparison.OrdinalIgnoreCase) < 0;
            var isSuccessful = containsPlanTag && !executeResultContext.ErrorOccurred;

            if (string.IsNullOrEmpty(results) && isComplete && isSuccessful)
            {
                results = executeResultContext.Variables.ToString();
            }
            else if (executeResultContext.ErrorOccurred)
            {
                results = executeResultContext.LastErrorDescription;
            }

            _ = context.Variables.UpdateWithPlanEntry(new SkillPlan
            {
                Id = planToExecute.Id,
                Goal = planToExecute.Goal,
                PlanString = planProgress,
                IsComplete = isComplete,
                IsSuccessful = isSuccessful,
                Result = results,
            });

            return context;
        }
        catch (PlanningException e)
        {
            switch (e.ErrorCode)
            {
                case PlanningException.ErrorCodes.InvalidPlan:
                    context.Log.LogWarning("[InvalidPlan] Error executing plan: {0} ({1})", e.Message, e.GetType().Name);
                    _ = context.Variables.UpdateWithPlanEntry(new SkillPlan
                    {
                        Id = Guid.NewGuid().ToString("N"),
                        Goal = planToExecute.Goal,
                        PlanString = planToExecute.PlanString,
                        IsComplete = true, // Plan was invalid, mark complete so it's not attempted further.
                        IsSuccessful = false,
                        Result = e.Message,
                    });

                    return context;
                case PlanningException.ErrorCodes.UnknownError:
                case PlanningException.ErrorCodes.InvalidConfiguration:
                    context.Log.LogWarning("[UnknownError] Error executing plan: {0} ({1})", e.Message, e.GetType().Name);
                    break;
                default:
                    throw;
            }
        }
        catch (Exception e) when (!e.IsCriticalException())
        {
            context.Log.LogWarning("Error executing plan: {0} ({1})", e.Message, e.GetType().Name);
            _ = context.Variables.UpdateWithPlanEntry(new SkillPlan
            {
                Id = Guid.NewGuid().ToString("N"),
                Goal = planToExecute.Goal,
                PlanString = planToExecute.PlanString,
                IsComplete = false,
                IsSuccessful = false,
                Result = e.Message,
            });

            return context;
        }

        return context;
    }
}

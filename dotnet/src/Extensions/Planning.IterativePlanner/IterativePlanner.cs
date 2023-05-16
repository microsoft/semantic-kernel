// Copyright (c) Microsoft. All rights reserved.
// Attempt to implement MRKL systems as described in https://arxiv.org/pdf/2205.00445.pdf
// strongly inspired by https://github.com/hwchase17/langchain/tree/master/langchain/agents/mrkl

using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Planning.IterativePlanner;


#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planning;
#pragma warning restore IDE0130

/// <summary>
/// A planner that uses semantic function to create a sequential plan.
/// </summary>
public sealed class IterativePlanner
{
    private readonly int _maxIterations;
    private const string StopSequence = "Observation:";

    private static string NormalizeLineEndings(string src)
    {
        return src.Replace("\r\n", "\n");
    }
    /// <summary>
    /// Initialize a new instance of the <see cref="IterativePlanner"/> class.
    /// </summary>
    /// <param name="kernel">The semantic kernel instance.</param>
    /// <param name="maxIterations"></param>
    /// <param name="config">The planner configuration.</param>
    /// <param name="prompt">Optional prompt override</param>
    public IterativePlanner(
        IKernel kernel,
        int maxIterations = 5,
        IterativePlannerConfig? config = null,
        string? prompt = null)
    {
        this._maxIterations = maxIterations;
        Verify.NotNull(kernel);
        this.Config = config ?? new();

        //this.Config.ExcludedSkills.Add(RestrictedSkillName);

        string promptTemplate = prompt ?? EmbeddedResource.Read("skprompt.txt");

        promptTemplate = NormalizeLineEndings(promptTemplate);
        this._functionFlowFunction = kernel.CreateSemanticFunction(
            promptTemplate: promptTemplate,
            //skillName: RestrictedSkillName,
            description: "Given a request or command or goal generate a step by step plan to " +
                         "fulfill the request using functions. This ability is also known as decision making and function flow",
            maxTokens: this.Config.MaxTokens,
            temperature: 0.0,
            stopSequences: new[] { StopSequence }
        );

        this._context = kernel.CreateNewContext();
        this._kernel = kernel;
        this.Steps = new List<NextStep>();
    }

    /// <summary>
    /// Create a plan for a goal.
    /// </summary>
    /// <param name="goal">The goal to create a plan for.</param>
    /// <returns>The plan.</returns>
    public async Task<string> ExecutePlanAsync(string goal)
    {
        if (string.IsNullOrEmpty(goal))
        {
            throw new PlanningException(PlanningException.ErrorCodes.InvalidGoal, "The goal specified is empty");
        }

        (string toolNames, string toolDescriptions) = await this.GetToolNamesAndDescriptionsAsync().ConfigureAwait(false);

        this._context.Variables.Set("toolNames", toolNames);
        this._context.Variables.Set("toolDescriptions", toolDescriptions);
        this._context.Variables.Set("question", goal);

        for (int i = 0; i < this._maxIterations; i++)
        {
            var scratchPad = this.CreateScratchPad(goal);
            Thread.Sleep(1000);
            PrintColored(scratchPad);
            this._context.Variables.Set("agentScratchPad", scratchPad);
            var llmResponse = await this._functionFlowFunction.InvokeAsync(this._context).ConfigureAwait(false);
            string actionText = llmResponse.Result.Trim();
            Thread.Sleep(1000);
            PrintColored(actionText);
            
            var nextStep = this.ParseResult(actionText);
            this.Steps.Add(nextStep);

            if (!String.IsNullOrEmpty(nextStep.FinalAnswer))
            {
                return nextStep.FinalAnswer;
            }

            nextStep.Observation = await this.InvokeActionAsync(nextStep.Action, nextStep.ActionInput).ConfigureAwait(false);
        }

        return "Result Not found";
    }

    private string CreateScratchPad(string goal)
    {
        if (this.Steps.Count == 0)
        {
            return string.Empty;
        }

        var result = new StringBuilder("This was your previous work (but I haven't seen any of it! I only see what you return as final answer):");
        result.AppendLine();
        result.AppendLine("Question: " + goal);
        foreach (var step in this.Steps)
        {
            result.AppendLine("Thought: " + step.OriginalResponse);
            //result.AppendLine("Action: " + step.Action);
            //result.AppendLine("Input: " + step.ActionInput);
            result.AppendLine("Observation: " + step.Observation);
        }

        return result.ToString();
    }

    private async Task<string> InvokeActionAsync(string actionName, string actionActionInput)
    {
        var availableFunctions = await this._context.GetAvailableFunctionsAsync(this.Config).ConfigureAwait(false);
        //ugly hack - fix later
        var theFunction = availableFunctions.FirstOrDefault(x => x.Name == actionName);
        if (theFunction == null)
        {
            throw new Exception("no such function" + actionName);
        }

        var func = this._kernel.Func(theFunction.SkillName, theFunction.Name);
        var result = await func.InvokeAsync(actionActionInput).ConfigureAwait(false);
        PrintColored(result.Result);
        return result.Result;
    }

    private static void PrintColored(string planResultString)
    {
        var color = Console.ForegroundColor;
        Console.ForegroundColor = ConsoleColor.Yellow;
        Console.WriteLine(planResultString);

        Console.ForegroundColor = color;
    }

    private NextStep ParseResult(string input)
    {
        var result = new NextStep();
        result.OriginalResponse = input;
        //until Action:
        Regex untilAction = new Regex(@"(.*)(?=Action:)", RegexOptions.Singleline);
        Match untilActionMatch = untilAction.Match(input);

        if (input.StartsWith("Final Answer:"))
        {
            result.FinalAnswer = input;
            return result;
        }

        if (untilActionMatch.Success)
        {
            result.Thought = untilActionMatch.Value;
        }

        Regex actionRegex = new Regex(@"```(.*?)```", RegexOptions.Singleline);

        Match actionMatch = actionRegex.Match(input);
        if (actionMatch.Success)
        {
            var json = actionMatch.Value.Trim('`').Trim();
            ActionDetails actionDetails = JsonSerializer.Deserialize<ActionDetails>(json);
            result.Action = actionDetails.action;
            result.ActionInput = actionDetails.action_input;
        }
        else
        {
            throw new Exception("no action found");
        }
        
        if (result.Action == "Final Answer")
        {
            result.FinalAnswer = result.ActionInput;
        }

        return result;
    }

    private async Task<(string, string)> GetToolNamesAndDescriptionsAsync()
    {
        var availableFunctions = await this._context.GetAvailableFunctionsAsync(this.Config).ConfigureAwait(false);
        //ugly hack - fix later
        var filtered = availableFunctions.Where(x => !x.Name.StartsWith("func")).ToList();
        string toolNames = String.Join(", ", filtered.Select(x => x.Name));
        string toolDescriptions = ">" + String.Join("\n>", filtered.Select(x => x.Name + ": " + x.Description)); 
        return (toolNames, toolDescriptions);
    }

    private IterativePlannerConfig Config { get; }

    private readonly SKContext _context;

    /// <summary>
    /// the function flow semantic function, which takes a goal and creates an xml plan that can be executed
    /// </summary>
    private readonly ISKFunction _functionFlowFunction;

    private readonly IKernel _kernel;
    public List<NextStep> Steps { get; set; }

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    //private const string RestrictedSkillName = "SequentialPlanner_Excluded";
}

public class ActionDetails
{
    public string action { get; set; }
    public string action_input { get; set; }
}
public class NextStep   
{
    public string Thought { get; set; }
    public string Action { get; set; }
    public string ActionInput { get; set; }
    public string Observation { get; set; }
    public string FinalAnswer { get; set; }
    public string OriginalResponse { get; set; }
}

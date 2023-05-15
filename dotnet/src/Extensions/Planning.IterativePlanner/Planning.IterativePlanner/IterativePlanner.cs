// Copyright (c) Microsoft. All rights reserved.
// Attempt to implement MRKL systems as described in arxiv.org/pdf/2205.00445.pdf
// strongly inspired by https://github.com/hwchase17/langchain/tree/master/langchain/agents/mrkl

using System.Reflection.Metadata.Ecma335;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Microsoft.SemanticKernel.SkillDefinition;
using Planning.IterativePlanner;

// namespace Planning.IterativePlanner;
namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// A planner that uses semantic function to create a sequential plan.
/// </summary>
public sealed class IterativePlanner
{
    private readonly int _maxIterations;
    private const string StopSequence = "Observation:";

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
        _maxIterations = maxIterations;
        Verify.NotNull(kernel);
        this.Config = config ?? new();

        //this.Config.ExcludedSkills.Add(RestrictedSkillName);

        string promptTemplate = prompt ?? EmbeddedResource.Read("skprompt.txt");

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

        (string toolNames, string toolDescriptions) = await GetToolNamesAndDescriptionsAsync();
       
       
        this._context.Variables.Set("toolNames", toolNames);
        this._context.Variables.Set("toolDescriptions", toolDescriptions);
        this._context.Variables.Set("question", goal);

        List<NextStep> steps = new List<NextStep>();
        for (int i = 0; i < _maxIterations; i++)
        {

            var scratchPad = CreateScratchPad(steps, goal);
            Thread.Sleep(1000);
            PrintColored(scratchPad);
            this._context.Variables.Set("agentScratchPad", scratchPad);
            var llmResponse = await this._functionFlowFunction.InvokeAsync(this._context).ConfigureAwait(false);
            string actionText = llmResponse.Result.Trim();
            Thread.Sleep(1000);
            PrintColored(actionText);
            
            var nextStep = ParseResult(actionText);
            steps.Add(nextStep);

            if (!String.IsNullOrEmpty(nextStep.FinalAnswer))
                return nextStep.FinalAnswer;

            nextStep.Observation = await  InvokeActionAsync(nextStep.Action, nextStep.ActionInput);

          

        }

        
        return "buha";
        //try
        //{
        //    var plan = planResultString.ToPlanFromXml(goal, this._context);
        //    //return plan;
        //}
        //catch (Exception e)
        //{
        //    throw new PlanningException(PlanningException.ErrorCodes.InvalidPlan, "Plan parsing error, invalid XML", e);
        //}
    }

    private string CreateScratchPad(List<NextStep> steps, string goal)
    {
        if(steps.Count==0)
            return string.Empty;

        var result = new StringBuilder("This was your previous work (but I haven't seen any of it! I only see what you return as final answer):");
        result.AppendLine();
        result.AppendLine("Question: " + goal);
        foreach (var step in steps)
        {
            result.AppendLine("Thought: "+ step.OriginalResponse);
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
            throw new Exception("no such function" + actionName);

        var func = _kernel.Func(theFunction.SkillName, theFunction.Name);
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

        //                                   @"```(.*?)```"
         Regex actionRegex = new Regex(@"```(.*?)```", RegexOptions.Singleline);
        //Regex actionRegex = new Regex(@"(?<=```).+?(?=```)", RegexOptions.Singleline);

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
        
        if(result.Action== "Final Answer")
            result.FinalAnswer = result.ActionInput;

        return result;
    }

    private async Task<(string, string)> GetToolNamesAndDescriptionsAsync()
    {
        var avaialbleFunctions = await this._context.GetAvailableFunctionsAsync(this.Config).ConfigureAwait(false);
        //ugly hack - fix later
        var filtered = avaialbleFunctions.Where(x => !x.Name.StartsWith("func")).ToList();
        string toolNames = String.Join(", ", filtered.Select(x=>x.Name));
        string toolDescriptions = ">"+ String.Join("\n>", filtered.Select(x => x.Name + ": " + x.Description)); 
        return (toolNames, toolDescriptions);

    }

  

    private IterativePlannerConfig Config { get; }

    private readonly SKContext _context;

    /// <summary>
    /// the function flow semantic function, which takes a goal and creates an xml plan that can be executed
    /// </summary>
    private readonly ISKFunction _functionFlowFunction;

    private readonly IKernel _kernel;

    /// <summary>
    /// The name to use when creating semantic functions that are restricted from plan creation
    /// </summary>
    //private const string RestrictedSkillName = "SequentialPlanner_Excluded";

    private const string Prefix =
        @"Answer the following questions as best you can. You have access to the following tools:
{tool_descriptions}";
    private const string ToolFormatInstructions = @"the way you use the tools is by specifying a json blob.
Specifically, this json should have a `action` key (with the name of the tool to use) and a `action_input` key (with the input to the tool going here).

The only values that should be in the ""action"" field are: {tool_names}

The $JSON_BLOB should only contain a SINGLE action, do NOT return a list of multiple actions. Here is an example of a valid $JSON_BLOB:

```
{{{{
  ""action"": $TOOL_NAME,
  ""action_input"": $INPUT
}}}}
```

ALWAYS use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action:
```
$JSON_BLOB
```
Observation: the result of the action
... (this Thought/Action/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question";


    private const string ToolSuffix = @"Begin! Reminder to always use the exact characters `Final Answer` when responding.";


    private const string FormatInstructions = @"Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question";

    private const string Suffix = @"Begin!

Question: {input}
Thought:{agent_scratchpad}";


    private const string ToolPrefix =
        "Answer the following questions as best you can. You have access to the following tools:";


  


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

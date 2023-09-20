// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning.Action;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planning;
#pragma warning restore IDE0130

/// <summary>
/// Action Planner allows to select one function out of many, to achieve a given goal.
/// The planner implement the Intent Detection pattern, uses the functions registered
/// in the kernel to see if there's a relevant one, providing instructions to call the
/// function and the rationale used to select it. The planner can also return
/// "no function" is nothing relevant is available.
/// The rationale is currently available only in the prompt, we might include it in
/// the Plan object in future.
/// </summary>
public sealed class ActionPlanner : IActionPlanner
{
    private const string StopSequence = "#END-OF-PLAN";
    private const string PluginName = "this";

    /// <summary>
    /// The regular expression for extracting serialized plan.
    /// </summary>
    private static readonly Regex s_planRegex = new("^[^{}]*(((?'Open'{)[^{}]*)+((?'Close-Open'})[^{}]*)+)*(?(Open)(?!))", RegexOptions.Singleline | RegexOptions.Compiled);

    // Planner semantic function
    private readonly ISKFunction _plannerFunction;

    // Context used to access the list of functions in the kernel
    private readonly SKContext _context;
    private readonly IKernel _kernel;
    private readonly ILogger _logger;

    // TODO: allow to inject skill store
    /// <summary>
    /// Initialize a new instance of the <see cref="ActionPlanner"/> class.
    /// </summary>
    /// <param name="kernel">The semantic kernel instance.</param>
    /// <param name="config">The planner configuration.</param>
    /// <param name="prompt">Optional prompt override</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public ActionPlanner(
        IKernel kernel,
        ActionPlannerConfig? config = null,
        string? prompt = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(kernel);

        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(ActionPlanner)) : NullLogger.Instance;

        string promptTemplate = prompt ?? EmbeddedResource.Read("skprompt.txt");

        this._plannerFunction = kernel.CreateSemanticFunction(
            pluginName: PluginName,
            promptTemplate: promptTemplate,
            maxTokens: 1024,
            stopSequences: new[] { StopSequence });

        kernel.ImportPlugin(this, pluginName: PluginName);

        this._kernel = kernel;
        this._context = kernel.CreateNewContext();

        // Set up Config with default values and excluded skills
        this._config = config ?? new();
        this._config.ExcludedPlugins.Add(PluginName);
    }

    /// <inheritdoc />
    public async Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(goal))
        {
            throw new SKException("The goal specified is empty");
        }

        this._context.Variables.Update(goal);

        SKContext result = await this._plannerFunction.InvokeAsync(this._context, cancellationToken: cancellationToken).ConfigureAwait(false);
        ActionPlanResponse? planData = this.ParsePlannerResult(result);

        if (planData == null)
        {
            throw new SKException("The plan deserialized to a null object");
        }

        // Build and return plan
        Plan plan;
        if (planData.Plan.Function.Contains("."))
        {
            var parts = planData.Plan.Function.Split('.');
            plan = new Plan(goal, this._context.Functions!.GetFunction(parts[0], parts[1]));
        }
        else if (!string.IsNullOrWhiteSpace(planData.Plan.Function))
        {
            plan = new Plan(goal, this._context.Functions!.GetFunction(planData.Plan.Function));
        }
        else
        {
            // No function was found - return a plan with no steps.
            plan = new Plan(goal);
        }

        // Populate plan parameters using the function and the parameters suggested by the planner
        if (plan.Steps.Count > 0)
        {
            foreach (KeyValuePair<string, object> p in planData.Plan.Parameters)
            {
                if (p.Value != null)
                {
                    plan.Steps[0].Parameters[p.Key] = p.Value.ToString();
                }
            }
        }

        return plan;
    }

    // TODO: use goal to find relevant functions in a skill store
    /// <summary>
    /// Native function returning a list of all the functions in the current context,
    /// excluding functions in the planner itself.
    /// </summary>
    /// <param name="goal">Currently unused. Will be used to handle long lists of functions.</param>
    /// <param name="context">Function execution context</param>
    /// <returns>List of functions, formatted accordingly to the prompt</returns>
    [SKFunction, Description("List all functions available in the kernel")]
    public string ListOfFunctions(
        [Description("The current goal processed by the planner")] string goal,
        SKContext context)
    {
        // Prepare list using the format used by skprompt.txt
        var list = new StringBuilder();
        var availableFunctions = this.GetAvailableFunctions(context);
        this.PopulateList(list, availableFunctions);

        return list.ToString();
    }

    // TODO: generate string programmatically
    // TODO: use goal to find relevant examples
    /// <summary>
    /// Native function that provides a list of good examples of plans to generate.
    /// </summary>
    /// <param name="goal">The current goal processed by the planner.</param>
    /// <param name="context">Function execution context.</param>
    /// <returns>List of good examples, formatted accordingly to the prompt.</returns>
    [SKFunction, Description("List a few good examples of plans to generate")]
    public string GoodExamples(
        [Description("The current goal processed by the planner")] string goal,
        SKContext context)
    {
        return @"
[EXAMPLE]
- List of functions:
// Read a file.
FileIOSkill.ReadAsync
Parameter ""path"": Source file.
// Write a file.
FileIOSkill.WriteAsync
Parameter ""path"": Destination file. (default value: sample.txt)
Parameter ""content"": File content.
// Get the current time.
TimePlugin.Time
No parameters.
// Makes a POST request to a uri.
HttpSkill.PostAsync
Parameter ""body"": The body of the request.
- End list of functions.
Goal: create a file called ""something.txt"".
{""plan"":{
""rationale"": ""the list contains a function that allows to create files"",
""function"": ""FileIOSkill.WriteAsync"",
""parameters"": {
""path"": ""something.txt"",
""content"": null
}}}
#END-OF-PLAN
";
    }

    // TODO: generate string programmatically
    /// <summary>
    /// Native function that provides a list of edge case examples of plans to handle.
    /// </summary>
    /// <param name="goal">The current goal processed by the planner.</param>
    /// <param name="context">Function execution context.</param>
    /// <returns>List of edge case examples, formatted accordingly to the prompt.</returns>
    [SKFunction, Description("List a few edge case examples of plans to handle")]
    public string EdgeCaseExamples(
        [Description("The current goal processed by the planner")] string goal,
        SKContext context)
    {
        return @"
[EXAMPLE]
- List of functions:
// Get the current time.
TimePlugin.Time
No parameters.
// Write a file.
FileIOSkill.WriteAsync
Parameter ""path"": Destination file. (default value: sample.txt)
Parameter ""content"": File content.
// Makes a POST request to a uri.
HttpSkill.PostAsync
Parameter ""body"": The body of the request.
// Read a file.
FileIOSkill.ReadAsync
Parameter ""path"": Source file.
- End list of functions.
Goal: tell me a joke.
{""plan"":{
""rationale"": ""the list does not contain functions to tell jokes or something funny"",
""function"": """",
""parameters"": {
}}}
#END-OF-PLAN
";
    }

    #region private ================================================================================

    /// <summary>
    /// The configuration for the ActionPlanner
    /// </summary>
    private ActionPlannerConfig _config { get; }

    /// <summary>
    /// Native function that filters out good JSON from planner result in case additional text is present
    /// using a similar regex to the balancing group regex defined here: https://learn.microsoft.com/en-us/dotnet/standard/base-types/grouping-constructs-in-regular-expressions#balancing-group-definitions
    /// </summary>
    /// <param name="plannerResult">Result context of planner function.</param>
    /// <returns>Instance of <see cref="ActionPlanResponse"/> object deserialized from extracted JSON.</returns>
    private ActionPlanResponse? ParsePlannerResult(SKContext plannerResult)
    {
        Match match = s_planRegex.Match(plannerResult.ToString());

        if (match.Success && match.Groups["Close"].Length > 0)
        {
            string planJson = $"{{{match.Groups["Close"]}}}";
            try
            {
                return JsonSerializer.Deserialize<ActionPlanResponse?>(planJson, new JsonSerializerOptions
                {
                    AllowTrailingCommas = true,
                    DictionaryKeyPolicy = null,
                    DefaultIgnoreCondition = JsonIgnoreCondition.Never,
                    PropertyNameCaseInsensitive = true,
                });
            }
            catch (Exception e)
            {
                throw new SKException("Plan parsing error, invalid JSON", e);
            }
        }
        else
        {
            throw new SKException($"Failed to extract valid json string from planner result: '{plannerResult}'");
        }
    }

    private void PopulateList(StringBuilder list, IEnumerable<FunctionView> functions)
    {
        foreach (FunctionView func in functions)
        {
            // Function description
            if (func.Description != null)
            {
                list.AppendLine($"// {AddPeriod(func.Description)}");
            }
            else
            {
                this._logger.LogWarning("{0}.{1} is missing a description", func.PluginName, func.Name);
                list.AppendLine($"// Function {func.PluginName}.{func.Name}.");
            }

            // Function name
            list.AppendLine($"{func.PluginName}.{func.Name}");

            // Function parameters
            foreach (var p in func.Parameters)
            {
                var description = string.IsNullOrEmpty(p.Description) ? p.Name : p.Description!;
                var defaultValueString = string.IsNullOrEmpty(p.DefaultValue) ? string.Empty : $" (default value: {p.DefaultValue})";
                list.AppendLine($"Parameter \"{p.Name}\": {AddPeriod(description)} {defaultValueString}");
            }
        }
    }

    private static string AddPeriod(string x)
    {
        return x.EndsWith(".", StringComparison.Ordinal) ? x : $"{x}.";
    }

    private IOrderedEnumerable<FunctionView> GetAvailableFunctions(SKContext context)
    {
        Verify.NotNull(context.Functions);

        var excludedSkills = this._config.ExcludedPlugins ?? new();
        var excludedFunctions = this._config.ExcludedFunctions ?? new();

        var availableFunctions = context.Functions.GetFunctionViews()
                .Where(s => !excludedSkills.Contains(s.PluginName, StringComparer.CurrentCultureIgnoreCase)
                    && !excludedFunctions.Contains(s.Name, StringComparer.CurrentCultureIgnoreCase))
                .OrderBy(x => x.PluginName)
                .ThenBy(x => x.Name);

        return availableFunctions;
    }

    #endregion
}

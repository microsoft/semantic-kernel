// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Planning.Action;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Action Planner allows to select one function out of many, to achieve a given goal.
/// The planner implement the Intent Detection pattern, uses the functions registered
/// in the kernel to see if there's a relevant one, providing instructions to call the
/// function and the rationale used to select it. The planner can also return
/// "no function" is nothing relevant is available.
/// The rationale is currently available only in the prompt, we might include it in
/// the Plan object in future.
/// </summary>
public sealed class ActionPlanner
{
    private const string StopSequence = "#END-OF-PLAN";
    private const string PluginName = "this";

    /// <summary>
    /// The regular expression for extracting serialized plan.
    /// </summary>
    private static readonly Regex s_planRegex = new("^[^{}]*(((?'Open'{)[^{}]*)+((?'Close-Open'})[^{}]*)+)*(?(Open)(?!))", RegexOptions.Singleline | RegexOptions.Compiled);

    /// <summary>Deserialization options for use with <see cref="ActionPlanResponse"/>.</summary>
    private static readonly JsonSerializerOptions s_actionPlayResponseOptions = new()
    {
        AllowTrailingCommas = true,
        DictionaryKeyPolicy = null,
        DefaultIgnoreCondition = JsonIgnoreCondition.Never,
        PropertyNameCaseInsensitive = true,
    };

    // Planner semantic function
    private readonly KernelFunction _plannerFunction;

    private readonly ContextVariables _contextVariables;
    private readonly Kernel _kernel;
    private readonly ILogger _logger;

    // TODO: allow to inject plugin store
    /// <summary>
    /// Initialize a new instance of the <see cref="ActionPlanner"/> class.
    /// </summary>
    /// <param name="kernel">The semantic kernel instance.</param>
    /// <param name="config">The planner configuration.</param>
    public ActionPlanner(
        Kernel kernel,
        ActionPlannerConfig? config = null)
    {
        Verify.NotNull(kernel);
        this._kernel = kernel;

        // Set up Config with default values and excluded plugins
        this.Config = config ?? new();
        this.Config.ExcludedPlugins.Add(PluginName);

        string promptTemplate = this.Config.GetPromptTemplate?.Invoke() ?? EmbeddedResource.Read("Action.skprompt.txt");

        this._plannerFunction = kernel.CreateFunctionFromPrompt(
            promptTemplate: promptTemplate,
            new PromptExecutionSettings()
            {
                ExtensionData = new()
                {
                    { "StopSequences", new[] { StopSequence } },
                    { "MaxTokens", this.Config.MaxTokens },
                }
            });

        kernel.ImportPluginFromObject(this, pluginName: PluginName);

        // Create context and logger
        this._contextVariables = new ContextVariables();
        this._logger = kernel.LoggerFactory.CreateLogger(this.GetType()) ?? NullLogger.Instance;
    }

    /// <summary>Creates a plan for the specified goal.</summary>
    /// <param name="goal">The goal for which a plan should be created.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The created plan.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="goal"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="goal"/> is empty or entirely composed of whitespace.</exception>
    /// <exception cref="KernelException">A plan could not be created.</exception>
    public Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(goal);

        return PlannerInstrumentation.CreatePlanAsync(
            static (ActionPlanner planner, string goal, CancellationToken cancellationToken) => planner.CreatePlanCoreAsync(goal, cancellationToken),
            static (Plan plan) => plan.ToSafePlanString(),
            this, goal, this._logger, cancellationToken);
    }

    private async Task<Plan> CreatePlanCoreAsync(string goal, CancellationToken cancellationToken)
    {
        this._contextVariables.Update(goal);

        FunctionResult result = await this._plannerFunction.InvokeAsync(this._kernel, this._contextVariables, cancellationToken: cancellationToken).ConfigureAwait(false);
        ActionPlanResponse? planData = this.ParsePlannerResult(result);

        if (planData == null)
        {
            throw new KernelException("The plan deserialized to a null object");
        }

        // Build and return plan
        Plan? plan = null;

        FunctionUtils.SplitPluginFunctionName(planData.Plan.Function, out var pluginName, out var functionName);
        if (!string.IsNullOrEmpty(functionName))
        {
            var getFunctionCallback = this.Config.GetFunctionCallback ?? this._kernel.Plugins.GetFunctionCallback();
            var pluginFunction = getFunctionCallback(pluginName, functionName);
            if (pluginFunction != null)
            {
                plan = new Plan(goal, pluginFunction);
                plan.Steps[0].PluginName = pluginName;
            }
        }

        plan ??= new(goal);

        // Populate plan parameters using the function and the parameters suggested by the planner
        if (plan.Steps.Count > 0)
        {
            foreach (KeyValuePair<string, object> p in planData.Plan.Parameters)
            {
                if (p.Value?.ToString() is string value)
                {
                    plan.Steps[0].Parameters[p.Key] = value;
                }
            }
        }

        return plan;
    }

    // TODO: use goal to find relevant functions in a plugin store
    /// <summary>
    /// Native function returning a list of all the functions in the current context,
    /// excluding functions in the planner itself.
    /// </summary>
    /// <param name="goal">Currently unused. Will be used to handle long lists of functions.</param>
    /// <param name="cancellationToken">The token to use to request cancellation.</param>
    /// <returns>List of functions, formatted accordingly to the prompt</returns>
    [KernelFunction, Description("List all functions available in the kernel")]
    public async Task<string> ListOfFunctionsAsync(
        [Description("The current goal processed by the planner")] string goal,
        CancellationToken cancellationToken = default)
    {
        // Prepare list using the format used by skprompt.txt
        var list = new StringBuilder();
        var availableFunctions = await this._kernel.Plugins.GetFunctionsAsync(this.Config, goal, this._logger, cancellationToken).ConfigureAwait(false);
        this.PopulateList(list, availableFunctions);

        return list.ToString();
    }

    // TODO: generate string programmatically
    // TODO: use goal to find relevant examples
    /// <summary>
    /// Native function that provides a list of good examples of plans to generate.
    /// </summary>
    /// <param name="goal">The current goal processed by the planner.</param>
    /// <param name="variables">Function execution context variables.</param>
    /// <returns>List of good examples, formatted accordingly to the prompt.</returns>
    [KernelFunction, Description("List a few good examples of plans to generate")]
    public string GoodExamples(
        [Description("The current goal processed by the planner")] string goal,
        ContextVariables variables)
    {
        return @"
[EXAMPLE]
- List of functions:
// Read a file.
FileIOPlugin.ReadAsync
Parameter ""path"": Source file.
// Write a file.
FileIOPlugin.WriteAsync
Parameter ""path"": Destination file. (default value: sample.txt)
Parameter ""content"": File content.
// Get the current time.
TimePlugin.Time
No parameters.
// Makes a POST request to a uri.
HttpPlugin.PostAsync
Parameter ""body"": The body of the request.
- End list of functions.
Goal: create a file called ""something.txt"".
{""plan"":{
""rationale"": ""the list contains a function that allows to create files"",
""function"": ""FileIOPlugin.WriteAsync"",
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
    /// <param name="variables">Function execution context variables.</param>
    /// <returns>List of edge case examples, formatted accordingly to the prompt.</returns>
    [KernelFunction, Description("List a few edge case examples of plans to handle")]
    public string EdgeCaseExamples(
        [Description("The current goal processed by the planner")] string goal,
        ContextVariables variables)
    {
        return @"
[EXAMPLE]
- List of functions:
// Get the current time.
TimePlugin.Time
No parameters.
// Write a file.
FileIOPlugin.WriteAsync
Parameter ""path"": Destination file. (default value: sample.txt)
Parameter ""content"": File content.
// Makes a POST request to a uri.
HttpPlugin.PostAsync
Parameter ""body"": The body of the request.
// Read a file.
FileIOPlugin.ReadAsync
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
    private ActionPlannerConfig Config { get; }

    /// <summary>
    /// Native function that filters out good JSON from planner result in case additional text is present
    /// using a similar regex to the balancing group regex defined here: https://learn.microsoft.com/en-us/dotnet/standard/base-types/grouping-constructs-in-regular-expressions#balancing-group-definitions
    /// </summary>
    /// <param name="plannerResult">Result of planner function.</param>
    /// <returns>Instance of <see cref="ActionPlanResponse"/> object deserialized from extracted JSON.</returns>
    private ActionPlanResponse? ParsePlannerResult(FunctionResult plannerResult)
    {
        if (plannerResult.GetValue<string>() is string result)
        {
            Match match = s_planRegex.Match(result);

            if (match.Success && match.Groups["Close"] is { Length: > 0 } close)
            {
                string planJson = $"{{{close}}}";
                try
                {
                    return JsonSerializer.Deserialize<ActionPlanResponse?>(planJson, s_actionPlayResponseOptions);
                }
                catch (Exception e)
                {
                    throw new KernelException("Plan parsing error, invalid JSON", e);
                }
            }
        }

        throw new KernelException($"Failed to extract valid json string from planner result: '{plannerResult}'");
    }

    private void PopulateList(StringBuilder list, IEnumerable<KernelFunctionMetadata> functions)
    {
        foreach (KernelFunctionMetadata func in functions)
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

    #endregion
}

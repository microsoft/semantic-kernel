// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Standard Semantic Kernel callable plan.
/// Plan is used to create trees of <see cref="KernelFunction"/>s.
/// </summary>
[DebuggerDisplay("{DebuggerDisplay,nq}")]
public sealed class Plan : KernelFunction
{
    /// <summary>
    /// State of the plan
    /// </summary>
    [JsonPropertyName("state")]
    [JsonConverter(typeof(ContextVariablesConverter))]
    public ContextVariables State { get; } = new();

    /// <summary>
    /// Steps of the plan
    /// </summary>
    [JsonPropertyName("steps")]
    public IReadOnlyList<Plan> Steps => this._steps.AsReadOnly();

    /// <summary>
    /// Parameters for the plan, used to pass information to the next step
    /// </summary>
    [JsonPropertyName("parameters")]
    [JsonConverter(typeof(ContextVariablesConverter))]
    public ContextVariables Parameters { get; set; } = new();

    /// <summary>
    /// Outputs for the plan, used to pass information to the caller
    /// </summary>
    [JsonPropertyName("outputs")]
    public IList<string> Outputs { get; set; } = new List<string>();

    /// <summary>
    /// Gets whether the plan has a next step.
    /// </summary>
    [JsonIgnore]
    public bool HasNextStep => this.NextStepIndex < this.Steps.Count;

    /// <summary>
    /// Gets the next step index.
    /// </summary>
    [JsonPropertyName("next_step_index")]
    public int NextStepIndex { get; private set; }

    /// <inheritdoc/>
    [JsonPropertyName("plugin_name")]
    public string PluginName { get; set; } = string.Empty;

    /// <summary>
    /// Initializes a new instance of the <see cref="Plan"/> class with a goal description.
    /// </summary>
    /// <param name="goal">The goal of the plan used as description.</param>
    public Plan(string goal) : base(GetRandomPlanName(), goal)
    {
        this.PluginName = nameof(Plan);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Plan"/> class with a goal description and steps.
    /// </summary>
    /// <param name="goal">The goal of the plan used as description.</param>
    /// <param name="steps">The steps to add.</param>
    public Plan(string goal, params KernelFunction[] steps) : this(goal)
    {
        this.AddSteps(steps);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Plan"/> class with a goal description and steps.
    /// </summary>
    /// <param name="goal">The goal of the plan used as description.</param>
    /// <param name="steps">The steps to add.</param>
    public Plan(string goal, params Plan[] steps) : this(goal)
    {
        this.AddSteps(steps);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Plan"/> class with a function.
    /// </summary>
    /// <param name="function">The function to execute.</param>
    public Plan(KernelFunction function) : base(function.Name, function.Description, function.ModelSettings)
    {
        this.SetFunction(function);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Plan"/> class with a function and steps.
    /// </summary>
    /// <param name="name">The name of the plan.</param>
    /// <param name="pluginName">The name of the plugin.</param>
    /// <param name="description">The description of the plan.</param>
    /// <param name="nextStepIndex">The index of the next step.</param>
    /// <param name="state">The state of the plan.</param>
    /// <param name="parameters">The parameters of the plan.</param>
    /// <param name="outputs">The outputs of the plan.</param>
    /// <param name="steps">The steps of the plan.</param>
    [JsonConstructor]
    public Plan(
        string name,
        string pluginName,
        string description,
        int nextStepIndex,
        ContextVariables state,
        ContextVariables parameters,
        IList<string> outputs,
        IReadOnlyList<Plan> steps) : base(name, description)
    {
        this.PluginName = pluginName;
        this.Description = description;
        this.NextStepIndex = nextStepIndex;
        this.State = state;
        this.Parameters = parameters;
        this.Outputs = outputs;
        this._steps.Clear();
        this.AddSteps(steps.ToArray());
    }

    /// <summary>
    /// Deserialize a JSON string into a Plan object.
    /// TODO: the context should never be null, it's required internally
    /// </summary>
    /// <param name="json">JSON string representation of a Plan</param>
    /// <param name="plugins">The collection of available functions..</param>
    /// <param name="requireFunctions">Whether to require functions to be registered. Only used when context is not null.</param>
    /// <returns>An instance of a Plan object.</returns>
    /// <remarks>If Context is not supplied, plan will not be able to execute.</remarks>
    public static Plan FromJson(string json, IReadOnlySKPluginCollection? plugins = null, bool requireFunctions = true)
    {
        var plan = JsonSerializer.Deserialize<Plan>(json, s_includeFieldsOptions) ?? new Plan(string.Empty);

        if (plugins != null)
        {
            plan = SetAvailablePlugins(plan, plugins, requireFunctions);
        }

        return plan;
    }

    /// <summary>
    /// Get JSON representation of the plan.
    /// </summary>
    /// <param name="indented">Whether to emit indented JSON</param>
    /// <returns>Plan serialized using JSON format</returns>
    public string ToJson(bool indented = false) =>
        indented ?
            JsonSerializer.Serialize(this, JsonOptionsCache.WriteIndented) :
            JsonSerializer.Serialize(this);

    /// <summary>
    /// Adds one or more existing plans to the end of the current plan as steps.
    /// </summary>
    /// <param name="steps">The plans to add as steps to the current plan.</param>
    /// <remarks>
    /// When you add a plan as a step to the current plan, the steps of the added plan are executed after the steps of the current plan have completed.
    /// </remarks>
    public void AddSteps(params Plan[] steps)
    {
        this._steps.AddRange(steps);
    }

    /// <summary>
    /// Adds one or more new steps to the end of the current plan.
    /// </summary>
    /// <param name="steps">The steps to add to the current plan.</param>
    /// <remarks>
    /// When you add a new step to the current plan, it is executed after the previous step in the plan has completed. Each step can be a function call or another plan.
    /// </remarks>
    public void AddSteps(params KernelFunction[] steps)
    {
        this._steps.AddRange(steps.Select(step => step is Plan plan ? plan : new Plan(step)));
    }

    /// <summary>
    /// Runs the next step in the plan using the provided kernel instance and variables.
    /// </summary>
    /// <param name="kernel">The kernel instance to use for executing the plan.</param>
    /// <param name="variables">The variables to use for the execution of the plan.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task representing the asynchronous execution of the plan's next step.</returns>
    /// <remarks>
    /// This method executes the next step in the plan using the specified kernel instance and context variables.
    /// The context variables contain the necessary information for executing the plan, such as the functions and logger.
    /// The method returns a task representing the asynchronous execution of the plan's next step.
    /// </remarks>
    public Task<Plan> RunNextStepAsync(Kernel kernel, ContextVariables variables, CancellationToken cancellationToken = default)
    {
        var context = kernel.CreateNewContext(variables);

        return this.InvokeNextStepAsync(kernel, context, cancellationToken);
    }

    /// <summary>
    /// Invoke the next step of the plan
    /// </summary>
    /// <param name="kernel">The kernel</param>
    /// <param name="context">Context to use</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The updated plan</returns>
    /// <exception cref="SKException">If an error occurs while running the plan</exception>
    public async Task<Plan> InvokeNextStepAsync(Kernel kernel, SKContext context, CancellationToken cancellationToken = default)
    {
        if (this.HasNextStep)
        {
            await this.InternalInvokeNextStepAsync(kernel, context, cancellationToken).ConfigureAwait(false);
        }

        return this;
    }

    #region ISKFunction implementation

    /// <inheritdoc/>
    protected override SKFunctionMetadata GetMetadataCore()
    {
        if (this.Function is not null)
        {
            return this.Function.GetMetadata();
        }

        // The parameter mapping definitions from Plan -> Function
        var stepParameters = this.Steps.SelectMany(s => s.Parameters);

        // The parameter descriptions from the Function
        var stepDescriptions = this.Steps.SelectMany(s => s.GetMetadata().Parameters);

        // The parameters for the Plan
        var parameters = this.Parameters.Select(p =>
        {
            var matchingParameter = stepParameters.FirstOrDefault(sp => sp.Value.Equals($"${p.Key}", StringComparison.OrdinalIgnoreCase));
            var stepDescription = stepDescriptions.FirstOrDefault(sd => sd.Name.Equals(matchingParameter.Key, StringComparison.OrdinalIgnoreCase));

            return new SKParameterMetadata(p.Key)
            {
                Description = stepDescription?.Description,
                DefaultValue = stepDescription?.DefaultValue,
                IsRequired = stepDescription?.IsRequired ?? false,
                ParameterType = stepDescription?.ParameterType,
                Schema = stepDescription?.Schema,
            };
        }).ToList();

        return new(this.Name)
        {
            PluginName = this.PluginName,
            Description = this.Description,
            Parameters = parameters
        };
    }

    /// <inheritdoc/>
    protected override async Task<FunctionResult> InvokeCoreAsync(
        Kernel kernel,
        SKContext context,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        var result = new FunctionResult(this.Name, context);

        if (this.Function is not null)
        {
            // Merge state with the current context variables.
            // Then filter the variables to only those needed for the next step.
            // This is done to prevent the function from having access to variables that it shouldn't.
            AddVariablesToContext(this.State, context);
            var functionVariables = this.GetNextStepVariables(context.Variables, this);
            var functionContext = context.Clone(functionVariables);

            // Execute the step
            result = await this.Function
                .InvokeAsync(kernel, functionContext, requestSettings, cancellationToken)
                .ConfigureAwait(false);
            this.UpdateFunctionResultWithOutputs(result);
        }
        else
        {
            this.CallFunctionInvoking(context);
            if (KernelFunctionFromPrompt.IsInvokingCancelOrSkipRequested(context))
            {
                return new FunctionResult(this.Name, context);
            }

            // loop through steps and execute until completion
            while (this.HasNextStep)
            {
                AddVariablesToContext(this.State, context);
                var stepResult = await this.InternalInvokeNextStepAsync(kernel, context, cancellationToken).ConfigureAwait(false);

                // If a step was cancelled before invocation
                // Return the last result state of the plan.
                if (stepResult is null)
                {
                    if (context.FunctionInvokingHandler?.EventArgs?.IsSkipRequested ?? false)
                    {
                        continue;
                    }

                    return result;
                }

                this.UpdateContextWithOutputs(context);

                result = new FunctionResult(this.Name, context, context.Variables.Input);
                this.UpdateFunctionResultWithOutputs(result);
            }

            this.CallFunctionInvoked(result, context);
            if (KernelFunctionFromPrompt.IsInvokedCancelRequested(context))
            {
                return new FunctionResult(this.Name, context, result.Value);
            }
        }

        return result;
    }

    #endregion ISKFunction implementation

    /// <summary>
    /// Expand variables in the input string.
    /// </summary>
    /// <param name="variables">Variables to use for expansion.</param>
    /// <param name="input">Input string to expand.</param>
    /// <returns>Expanded string.</returns>
    internal string ExpandFromVariables(ContextVariables variables, string input)
    {
        var result = input;
        var matches = s_variablesRegex.Matches(input);
        var orderedMatches = matches.Cast<Match>().Select(m => m.Groups["var"].Value).Distinct().OrderByDescending(m => m.Length);

        foreach (var varName in orderedMatches)
        {
            if (variables.TryGetValue(varName, out string? value) || this.State.TryGetValue(varName, out value))
            {
                result = result.Replace($"${varName}", value);
            }
        }

        return result;
    }

    /// <summary>
    /// Invoke the next step of the plan
    /// </summary>
    /// <param name="kernel">The kernel</param>
    /// <param name="context">Context to use</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Next step result</returns>
    /// <exception cref="SKException">If an error occurs while running the plan</exception>
    private async Task<FunctionResult?> InternalInvokeNextStepAsync(Kernel kernel, SKContext context, CancellationToken cancellationToken = default)
    {
        if (this.HasNextStep)
        {
            var step = this.Steps[this.NextStepIndex];

            // Merge the state with the current context variables for step execution
            var functionVariables = this.GetNextStepVariables(context.Variables, step);

            // Execute the step
            var result = await kernel.RunAsync(step, functionVariables, cancellationToken).ConfigureAwait(false);
            if (result is null)
            {
                // Step was cancelled
                return null;
            }

            var resultValue = result.Context.Variables.Input.Trim();

            #region Update State

            // Update state with result
            this.State.Update(resultValue);

            // Update Plan Result in State with matching outputs (if any)
            if (this.Outputs.Intersect(step.Outputs).Any())
            {
                if (this.State.TryGetValue(DefaultResultKey, out string? currentPlanResult))
                {
                    this.State.Set(DefaultResultKey, $"{currentPlanResult}\n{resultValue}");
                }
                else
                {
                    this.State.Set(DefaultResultKey, resultValue);
                }
            }

            // Update state with outputs (if any)
            foreach (var item in step.Outputs)
            {
                if (result.Context.Variables.TryGetValue(item, out string? val))
                {
                    this.State.Set(item, val);
                }
                else
                {
                    this.State.Set(item, resultValue);
                }
            }

            #endregion Update State

            this.NextStepIndex++;

            return result;
        }

        throw new InvalidOperationException("There isn't a next step");
    }

    private void CallFunctionInvoking(SKContext context)
    {
        var eventWrapper = context.FunctionInvokingHandler;
        if (eventWrapper?.Handler is null)
        {
            return;
        }

        eventWrapper.EventArgs = new FunctionInvokingEventArgs(this.GetMetadata(), context);
        eventWrapper.Handler.Invoke(this, eventWrapper.EventArgs);
    }

    private void CallFunctionInvoked(FunctionResult result, SKContext context)
    {
        var eventWrapper = context.FunctionInvokedHandler;

        // Not handlers registered, return the result as is
        if (eventWrapper?.Handler is null)
        {
            return;
        }

        eventWrapper.EventArgs = new FunctionInvokedEventArgs(this.GetMetadata(), result);
        eventWrapper.Handler.Invoke(this, eventWrapper.EventArgs);

        // Updates the eventArgs metadata during invoked handler execution
        // will reflect in the result metadata
        result.Metadata = eventWrapper.EventArgs.Metadata;
    }

    /// <summary>
    /// Set functions for a plan and its steps.
    /// </summary>
    /// <param name="plan">Plan to set functions for.</param>
    /// <param name="plugins">The collection of available plugins.</param>
    /// <param name="requireFunctions">Whether to throw an exception if a function is not found.</param>
    /// <returns>The plan with functions set.</returns>
    private static Plan SetAvailablePlugins(Plan plan, IReadOnlySKPluginCollection plugins, bool requireFunctions = true)
    {
        if (plan.Steps.Count == 0)
        {
            Verify.NotNull(plugins);

            if (plugins.TryGetFunction(plan.PluginName, plan.Name, out var planFunction))
            {
                plan.SetFunction(planFunction);
            }
            else if (requireFunctions)
            {
                throw new SKException($"Function '{plan.PluginName}.{plan.Name}' not found in function collection");
            }
        }
        else
        {
            foreach (var step in plan.Steps)
            {
                SetAvailablePlugins(step, plugins, requireFunctions);
            }
        }

        return plan;
    }

    /// <summary>
    /// Add any missing variables from a plan state variables to the context.
    /// </summary>
    private static void AddVariablesToContext(ContextVariables vars, SKContext context)
    {
        // Loop through vars and add anything missing to context
        foreach (var item in vars)
        {
            if (!context.Variables.TryGetValue(item.Key, out string? value) || string.IsNullOrEmpty(value))
            {
                context.Variables.Set(item.Key, item.Value);
            }
        }
    }

    /// <summary>
    /// Update the context with the outputs from the current step.
    /// </summary>
    /// <param name="context">The context to update.</param>
    /// <returns>The updated context.</returns>
    private SKContext UpdateContextWithOutputs(SKContext context)
    {
        var resultString = this.State.TryGetValue(DefaultResultKey, out string? result) ? result : this.State.ToString();
        context.Variables.Update(resultString);

        // copy previous step's variables to the next step
        foreach (var item in this._steps[this.NextStepIndex - 1].Outputs)
        {
            if (this.State.TryGetValue(item, out string? val))
            {
                context.Variables.Set(item, val);
            }
            else
            {
                context.Variables.Set(item, resultString);
            }
        }

        return context;
    }

    /// <summary>
    /// Update the function result with the outputs from the current state.
    /// </summary>
    /// <param name="functionResult">The function result to update.</param>
    /// <returns>The updated function result.</returns>
    private FunctionResult? UpdateFunctionResultWithOutputs(FunctionResult? functionResult)
    {
        if (functionResult is null)
        {
            return null;
        }

        foreach (var output in this.Outputs)
        {
            if (this.State.TryGetValue(output, out var value))
            {
                functionResult.Metadata[output] = value;
            }
            else if (functionResult.Context.Variables.TryGetValue(output, out var val))
            {
                functionResult.Metadata[output] = val;
            }
        }

        return functionResult;
    }

    /// <summary>
    /// Get the variables for the next step in the plan.
    /// </summary>
    /// <param name="variables">The current context variables.</param>
    /// <param name="step">The next step in the plan.</param>
    /// <returns>The context variables for the next step in the plan.</returns>
    private ContextVariables GetNextStepVariables(ContextVariables variables, Plan step)
    {
        // Priority for Input
        // - Parameters (expand from variables if needed)
        // - SKContext.Variables
        // - Plan.State
        // - Empty if sending to another plan
        // - Plan.Description

        var input = string.Empty;
        if (!string.IsNullOrEmpty(step.Parameters.Input))
        {
            input = this.ExpandFromVariables(variables, step.Parameters.Input!);
        }
        else if (!string.IsNullOrEmpty(variables.Input))
        {
            input = variables.Input;
        }
        else if (!string.IsNullOrEmpty(this.State.Input))
        {
            input = this.State.Input;
        }
        else if (step.Steps.Count > 0)
        {
            input = string.Empty;
        }
        else if (!string.IsNullOrEmpty(this.Description))
        {
            input = this.Description;
        }

        var stepVariables = new ContextVariables(input);

        // Priority for remaining stepVariables is:
        // - Function Parameters (pull from variables or state by a key value)
        // - Step Parameters (pull from variables or state by a key value)
        // - All other variables. These are carried over in case the function wants access to the ambient content.
        var functionParameters = step.GetMetadata();
        foreach (var param in functionParameters.Parameters)
        {
            if (param.Name.Equals(ContextVariables.MainKey, StringComparison.OrdinalIgnoreCase))
            {
                continue;
            }

            if (variables.TryGetValue(param.Name, out string? value))
            {
                stepVariables.Set(param.Name, value);
            }
            else if (this.State.TryGetValue(param.Name, out value) && !string.IsNullOrEmpty(value))
            {
                stepVariables.Set(param.Name, value);
            }
        }

        foreach (var item in step.Parameters)
        {
            // Don't overwrite variable values that are already set
            if (stepVariables.ContainsKey(item.Key))
            {
                continue;
            }

            var expandedValue = this.ExpandFromVariables(variables, item.Value);
            if (!expandedValue.Equals(item.Value, StringComparison.OrdinalIgnoreCase))
            {
                stepVariables.Set(item.Key, expandedValue);
            }
            else if (variables.TryGetValue(item.Key, out string? value))
            {
                stepVariables.Set(item.Key, value);
            }
            else if (this.State.TryGetValue(item.Key, out value))
            {
                stepVariables.Set(item.Key, value);
            }
            else
            {
                stepVariables.Set(item.Key, expandedValue);
            }
        }

        foreach (KeyValuePair<string, string> item in variables)
        {
            if (!stepVariables.ContainsKey(item.Key))
            {
                stepVariables.Set(item.Key, item.Value);
            }
        }

        return stepVariables;
    }

    private void SetFunction(KernelFunction function)
    {
        this.Function = function;
        this.Name = function.Name;
        this.Description = function.Description;
    }

    private static string GetRandomPlanName() => "plan" + Guid.NewGuid().ToString("N");

    /// <summary>Deserialization options for including fields.</summary>
    private static readonly JsonSerializerOptions s_includeFieldsOptions = new() { IncludeFields = true };

    private KernelFunction? Function { get; set; }

    private readonly List<Plan> _steps = new();

    private static readonly Regex s_variablesRegex = new(@"\$(?<var>\w+)");

    private const string DefaultResultKey = "PLAN.RESULT";

    [DebuggerBrowsable(DebuggerBrowsableState.Never)]
    private string DebuggerDisplay
    {
        get
        {
            string display = this.Description;

            if (!string.IsNullOrWhiteSpace(this.Name))
            {
                display = $"{this.Name} ({display})";
            }

            if (this._steps.Count > 0)
            {
                display += $", Steps = {this._steps.Count}, NextStep = {this.NextStepIndex}";
            }

            return display;
        }
    }
}

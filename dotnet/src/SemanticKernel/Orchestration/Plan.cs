// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Standard Semantic Kernel callable plan.
/// Plan is used to create trees of <see cref="ISKFunction"/>s.
/// </summary>
public class Plan : ISKFunction
{
    /// <summary>
    /// State of the plan
    /// </summary>
    [JsonPropertyName("state")]
    public ContextVariables State { get; } = new();

    /// <summary>
    /// Steps of the plan
    /// </summary>
    [JsonPropertyName("steps")]
    internal IReadOnlyList<ISKFunction> Steps => this._steps.AsReadOnly();

    /// <summary>
    /// Named parameters for the function
    /// </summary>
    [JsonPropertyName("named_parameters")]
    public ContextVariables NamedParameters { get; set; } = new();

    public bool HasNextStep => this.NextStepIndex < this.Steps.Count;

    protected int NextStepIndex { get; set; } = 0;

    #region ISKFunction implementation

    /// <inheritdoc/>
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    /// <inheritdoc/>
    [JsonPropertyName("skill_name")]
    public string SkillName { get; set; } = string.Empty;

    /// <inheritdoc/>
    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    /// <inheritdoc/>
    [JsonPropertyName("is_semantic")]
    public bool IsSemantic { get; internal set; } = false;

    /// <inheritdoc/>
    [JsonPropertyName("request_settings")]
    public CompleteRequestSettings RequestSettings { get; internal set; } = new();

    #endregion ISKFunction implementation

    /// <summary>
    /// Initializes a new instance of the <see cref="Plan"/> class with a goal description.
    /// </summary>
    /// <param name="goal">The goal of the plan used as description.</param>
    public Plan(string goal)
    {
        this.Description = goal;
        this.SkillName = this.GetType().FullName;
        this.Name = goal;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Plan"/> class with a goal description and steps.
    /// </summary>
    /// <param name="goal">The goal of the plan used as description.</param>
    /// <param name="steps">The steps to add.</param>
    [JsonConstructor]
    public Plan(string goal, params ISKFunction[] steps) : this(goal)
    {
        this.AddSteps(steps);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Plan"/> class with a function.
    /// </summary>
    /// <param name="function">The function to execute.</param>
    public Plan(ISKFunction function)
    {
        this.SetFunction(function);
    }

    /// <summary>
    /// Adds one or more new steps to the end of the current plan.
    /// </summary>
    /// <param name="steps">The steps to add to the current plan.</param>
    /// <remarks>
    /// When you add a new step to the current plan, it is executed after the previous step in the plan has completed. Each step can be a function call or another plan.
    /// </remarks>
    public void AddSteps(params ISKFunction[] steps)
    {
        foreach (var step in steps)
        {
            this._steps.Add(new Plan(step));
        }
    }

    /// <summary>
    /// Runs the next step in the plan using the provided kernel instance and variables.
    /// </summary>
    /// <param name="kernel">The kernel instance to use for executing the plan.</param>
    /// <param name="variables">The variables to use for the execution of the plan.</param>
    /// <param name="cancellationToken">The cancellation token to cancel the execution of the plan.</param>
    /// <returns>A task representing the asynchronous execution of the plan's next step.</returns>
    /// <remarks>
    /// This method executes the next step in the plan using the specified kernel instance and context variables. The context variables contain the necessary information for executing the plan, such as the memory, skills, and logger. The method returns a task representing the asynchronous execution of the plan's next step.
    /// </remarks>
    public Task<Plan> RunNextStepAsync(IKernel kernel, ContextVariables variables, CancellationToken cancellationToken = default)
    {
        var context = new SKContext(
            variables,
            kernel.Memory,
            kernel.Skills,
            kernel.Log,
            cancellationToken);
        return this.InvokeNextStepAsync(context);
    }

    #region ISKFunction implementation

    /// <inheritdoc/>
    public FunctionView Describe()
    {
        // TODO - Eventually, we should be able to describe a plan and it's expected inputs/outputs
        return this.Function?.Describe() ?? throw new NotImplementedException();
    }

    /// <inheritdoc/>
    public Task<SKContext> InvokeAsync(string input, SKContext? context = null, CompleteRequestSettings? settings = null, ILogger? log = null,
        CancellationToken? cancel = null)
    {
        context ??= new SKContext(new ContextVariables(input), null!, null, log ?? NullLogger.Instance, cancel ?? CancellationToken.None);
        return this.InvokeAsync(context, settings, log, cancel);
    }

    /// <inheritdoc/>
    public async Task<SKContext> InvokeAsync(SKContext? context = null, CompleteRequestSettings? settings = null, ILogger? log = null,
        CancellationToken? cancel = null)
    {
        context ??= new SKContext(new ContextVariables(), null!, null, log ?? NullLogger.Instance, cancel ?? CancellationToken.None);

        if (this.Function is not null)
        {
            var result = await this.Function.InvokeAsync(context, settings, log, cancel);

            if (result.ErrorOccurred)
            {
                result.Log.LogError(
                    result.LastException,
                    "Something went wrong in plan step {0}.{1}:'{2}'", this.SkillName, this.Name, context.LastErrorDescription);
                return result;
            }

            context.Variables.Update(result.Result.ToString());
        }
        else
        {
            // loop through steps and execute until completion
            while (this.HasNextStep)
            {
                var functionContext = context;
                // Loop through State and add anything missing to functionContext

                AddVariablesToContext(this.State, functionContext);

                await this.InvokeNextStepAsync(functionContext);

                context.Variables.Update(this.State.ToString());
            }
        }

        return context;
    }

    /// <inheritdoc/>
    public ISKFunction SetDefaultSkillCollection(IReadOnlySkillCollection skills)
    {
        return this.Function is null
            ? throw new NotImplementedException()
            : this.Function.SetDefaultSkillCollection(skills);
    }

    /// <inheritdoc/>
    public ISKFunction SetAIService(Func<ITextCompletion> serviceFactory)
    {
        return this.Function is null
            ? throw new NotImplementedException()
            : this.Function.SetAIService(serviceFactory);
    }

    /// <inheritdoc/>
    public ISKFunction SetAIConfiguration(CompleteRequestSettings settings)
    {
        return this.Function is null
            ? throw new NotImplementedException()
            : this.Function.SetAIConfiguration(settings);
    }

    #endregion ISKFunction implementation

    /// <summary>
    /// Invoke the next step of the plan
    /// </summary>
    /// <param name="context">Context to use</param>
    /// <returns>The updated plan</returns>
    /// <exception cref="KernelException">If an error occurs while running the plan</exception>
    public async Task<Plan> InvokeNextStepAsync(SKContext context)
    {
        if (this.HasNextStep)
        {
            var step = this.Steps[this.NextStepIndex];

            context = await step.InvokeAsync(context);

            if (context.ErrorOccurred)
            {
                throw new KernelException(KernelException.ErrorCodes.FunctionInvokeError,
                    $"Error occurred while running plan step: {context.LastErrorDescription}", context.LastException);
            }

            this.NextStepIndex++;
            this.State.Update(context.Result.Trim());
        }

        return this;
    }

    protected void SetFunction(ISKFunction function)
    {
        this.Function = function;
        this.Name = function.Name;
        this.SkillName = function.SkillName;
        this.Description = function.Description;
        this.IsSemantic = function.IsSemantic;
        this.RequestSettings = function.RequestSettings;
    }

    protected ISKFunction? Function { get; set; } = null;

    private List<ISKFunction> _steps = new();

    private static void AddVariablesToContext(ContextVariables vars, SKContext context)
    {
        foreach (var item in vars)
        {
            if (!context.Variables.ContainsKey(item.Key))
            {
                context.Variables.Set(item.Key, item.Value);
            }
        }
    }
}

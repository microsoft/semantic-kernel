// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// A plan class that is executable by the kernel
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
    public List<Plan> Steps { get; } = new();

    /// <summary>
    /// Named parameters for the function
    /// </summary>
    [JsonPropertyName("named_parameters")]
    public ContextVariables NamedParameters { get; set; } = new();

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
    public bool IsSemantic { get; protected set; } = false;

    /// <inheritdoc/>
    [JsonPropertyName("request_settings")]
    public CompleteRequestSettings RequestSettings { get; protected set; } = new();

    #endregion ISKFunction implementation

    public Plan(string goal)
    {
        this.Description = goal;
    }

    public Plan(ISKFunction function)
    {
        this.SetFunction(function);
    }

    /// <summary>
    /// Run the next step of the plan
    /// </summary>
    /// <param name="kernel">Kernel instance to use</param>
    /// <param name="variables">Variables to use</param>
    /// <param name="cancellationToken">Cancellation token</param>
    /// <returns>The updated plan</returns>
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
        return this.Function?.Describe() ?? new();
    }

    /// <inheritdoc/>
    public Task<SKContext> InvokeAsync(string input, SKContext? context = null, CompleteRequestSettings? settings = null, ILogger? log = null,
        CancellationToken? cancel = null)
    {
        if (this.Function is not null)
        {
            return this.Function.InvokeAsync(input, context, settings, log, cancel);
        }
        else
        {
            context ??= new SKContext(new ContextVariables(input), null!, null, log ?? NullLogger.Instance, cancel ?? CancellationToken.None);
            return this.InvokeAsync(context, settings, log, cancel);
        }
    }

    /// <inheritdoc/>
    public Task<SKContext> InvokeAsync(SKContext? context = null, CompleteRequestSettings? settings = null, ILogger? log = null,
        CancellationToken? cancel = null)
    {
        if (this.Function is not null)
        {
            return await this.Function.InvokeAsync(context, settings, log, cancel);
        }
        else
        {
            context ??= new SKContext(new ContextVariables(), null!, null, log ?? NullLogger.Instance, cancel ?? CancellationToken.None);

            // loop through steps and execute until completion
            while (this.Steps.Count > 0)
            {
                await this.InvokeNextStepAsync(context);
                context.Variables.Update(this.State.ToString());
            }

            return context;
        }
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
    protected virtual async Task<Plan> InvokeNextStepAsync(SKContext context)
    {
        if (this.Steps.Count > 0)
        {
            var step = this.Steps[0];
            this.Steps.RemoveAt(0);

            var stepResult = await step.InvokeAsync(context);

            this.State.Update(stepResult.Result.Trim());
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
}

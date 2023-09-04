// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Planning.PowerShell;

/// <summary>
/// A planner that uses semantic function to create a plan, based on PowerShell script.
/// </summary>
public class PowerShellPlanner
{
    /// <summary>
    /// Initializes a new instance of the <see cref="PowerShellPlanner"/> class.
    /// </summary>
    /// <param name="kernel">Instance of <see cref="IKernel"/>.</param>
    /// <param name="config">Instance of <see cref="PowerShellPlannerConfig"/> with planner configuration.</param>
    /// <param name="prompt">Optional planner prompt override.</param>
    public PowerShellPlanner(
        IKernel kernel,
        PowerShellPlannerConfig? config = null,
        string? prompt = null)
    {
        this.Config = config ?? new();

        this.Config.ExcludedSkills.Add(SkillName);

        string promptTemplate = prompt ?? EmbeddedResource.Read("skprompt.txt");

        this._generateScriptFunction = kernel.CreateSemanticFunction(
            promptTemplate: promptTemplate,
            skillName: SkillName,
            description: "Create PowerShell script to satisfy given goal",
            maxTokens: 1024,
            temperature: 0.0);

        this._context = kernel.CreateNewContext();
    }

    /// <summary>
    /// Create a plan for a goal.
    /// </summary>
    /// <param name="goal">The goal to create a plan for.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The plan.</returns>
    /// <exception cref="SKException">Thrown when the plan cannot be created.</exception>
    public async Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default)
    {
        var script = await this.GenerateScriptAsync(goal, cancellationToken).ConfigureAwait(false);

        var getSkillFunction = this.Config.GetSkillFunction ?? GetSkillFunction(this._context);
        var plan = script.ToPlanFromScript(goal, getSkillFunction);

        return plan;
    }

    #region private ================================================================================

    private const string SkillName = "PowerShell_Excluded";

    private PowerShellPlannerConfig Config { get; }

    private readonly SKContext _context;
    private readonly ISKFunction _generateScriptFunction;

    private async Task<string> GenerateScriptAsync(string goal, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrEmpty(goal))
        {
            throw new SKException("The goal specified is empty");
        }

        var availableFunctionsManual = this._context.GetFunctionsManual(this.Config);

        this._context.Variables.Set("available_functions", availableFunctionsManual);
        this._context.Variables.Update(goal);

        var scriptResult = await this._generateScriptFunction
            .InvokeAsync(this._context, cancellationToken: cancellationToken)
            .ConfigureAwait(false);

        var script = this.SanitizeScript(scriptResult.Result);

        return script;
    }

    private string SanitizeScript(string script)
    {
        const StringComparison ComparisonType = StringComparison.OrdinalIgnoreCase;

        const string MarkdownScriptPrefix = "```powershell";
        const string MarkdownScriptEnding = "```";

        if (script.StartsWith(MarkdownScriptPrefix, ComparisonType))
        {
            script = script.Replace(MarkdownScriptPrefix, string.Empty, ComparisonType);
        }

        if (script.EndsWith(MarkdownScriptEnding, ComparisonType))
        {
            script = script.Replace(MarkdownScriptEnding, string.Empty, ComparisonType);
        }

        return script;
    }

    private static Func<string, string, ISKFunction?> GetSkillFunction(SKContext context)
    {
        return (skillName, functionName) =>
        {
            if (string.IsNullOrEmpty(skillName))
            {
                if (context.Skills!.TryGetFunction(functionName, out var skillFunction))
                {
                    return skillFunction;
                }
            }
            else if (context.Skills!.TryGetFunction(skillName, functionName, out var skillFunction))
            {
                return skillFunction;
            }

            return null;
        };
    }

    #endregion
}

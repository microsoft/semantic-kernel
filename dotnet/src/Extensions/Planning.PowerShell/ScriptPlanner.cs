// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Planning.PowerShell;

public class ScriptPlanner
{
    public ScriptPlanner(
        IKernel kernel,
        ScriptPlannerConfig? config = null,
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

    public async Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default)
    {
        var script = await this.GenerateScriptAsync(goal, cancellationToken).ConfigureAwait(false);

        var getSkillFunction = this.Config.GetSkillFunction ?? ScriptParser.GetSkillFunction(this._context);
        var plan = script.ToPlanFromScript(goal, getSkillFunction);

        return plan;
    }

    #region private ================================================================================

    private const string SkillName = "PowerShell_Excluded";

    private ScriptPlannerConfig Config { get; }

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

    #endregion
}

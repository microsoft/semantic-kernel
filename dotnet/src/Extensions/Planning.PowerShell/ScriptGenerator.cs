// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Planning.PowerShell;

public class ScriptGenerator
{
    public ScriptGenerator(
        IKernel kernel,
        ScriptGenerationConfig? config = null,
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

    public async Task<string> GenerateScriptAsync(string goal, CancellationToken cancellationToken = default)
    {
        if (string.IsNullOrWhiteSpace(goal))
        {
            throw new PlanningException(PlanningException.ErrorCodes.InvalidGoal, "The goal specified is empty");
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
        const string MarkdownScriptPrefix = "```powershell";
        const string MarkdownScriptEnding = "```";

        if (script.StartsWith(MarkdownScriptPrefix, StringComparison.OrdinalIgnoreCase))
        {
            script = script.Replace(MarkdownScriptPrefix, string.Empty);
        }

        if (script.EndsWith(MarkdownScriptEnding, StringComparison.OrdinalIgnoreCase))
        {
            script = script.Replace(MarkdownScriptEnding, string.Empty);
        }

        return script;
    }

    private const string SkillName = "PowerShell_Excluded";

    private ScriptGenerationConfig Config { get; }

    private readonly SKContext _context;
    private readonly ISKFunction _generateScriptFunction;
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Management.Automation.Language;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Planning.PowerShell;

internal static class ScriptParser
{
    internal static Plan ToPlanFromScript(this string script, string goal, Func<string, string, ISKFunction?> getSkillFunction)
    {
        var plan = new Plan(goal);

        plan.OriginalPlan = script;

        var syntaxTree = Parser.ParseInput(script, out var tokens, out var errors);
        var resultVariable = string.Empty;

        foreach (var command in GetFunctionInvokationsFromScript(syntaxTree))
        {
            ValidateCommand(command);

            var parameterElements = GetParameterElements(command.CommandElements);

            GetSkillFunctionNames(parameterElements[UriParameterName], out var skillName, out var functionName);

            if (!string.IsNullOrWhiteSpace(functionName))
            {
                var skillFunction = getSkillFunction(skillName, functionName);
                var variables = GetVariables(parameterElements[BodyParameterName]);

                if (skillFunction != null)
                {
                    var planStep = new Plan(skillFunction);

                    var functionVariables = new ContextVariables();
                    var functionOutputs = new List<string>();
                    var functionResults = new List<string>();

                    var view = skillFunction.Describe();

                    foreach (var parameter in view.Parameters)
                    {
                        functionVariables.Set(parameter.Name, parameter.DefaultValue);
                    }

                    foreach (var variable in variables)
                    {
                        functionVariables.Set(variable.Key, variable.Value);
                    }

                    var outputVariable = GetOutputVariable(command);

                    if (outputVariable != null)
                    {
                        functionOutputs.Add(outputVariable);
                        resultVariable = outputVariable;
                    }

                    planStep.Outputs = functionOutputs;
                    planStep.Parameters = functionVariables;

                    plan.AddSteps(planStep);
                }
            }
        }

        plan.Outputs.Add(resultVariable);

        return plan;
    }

    internal static Func<string, string, ISKFunction?> GetSkillFunction(SKContext context)
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

    #region private ================================================================================

    private static Dictionary<string, CommandElementAst> GetParameterElements(ReadOnlyCollection<CommandElementAst> commandElements)
    {
        var result = new Dictionary<string, CommandElementAst>();

        for (var i = 0; i < commandElements.Count; i++)
        {
            if (commandElements[i] is CommandParameterAst parameter)
            {
                if (parameter.ParameterName.Equals(UriParameterName, StringComparison.Ordinal) ||
                    parameter.ParameterName.Equals(BodyParameterName, StringComparison.Ordinal))
                {
                    result.Add(parameter.ParameterName, commandElements[i + 1]);
                }
            }
        }

        return result;
    }

    private static void ValidateCommand(CommandAst command)
    {
        const string AllowedCommandName = "Invoke-RestMethod";

        var commandName = command.GetCommandName();

        if (!commandName.Equals(AllowedCommandName, StringComparison.Ordinal))
        {
            throw new SKException($"Script can contain only {AllowedCommandName} command.");
        }
    }

    private static IEnumerable<CommandAst> GetFunctionInvokationsFromScript(ScriptBlockAst syntaxTree)
    {
        return syntaxTree
            .FindAll(treeItem => treeItem is CommandAst command, searchNestedScriptBlocks: true)
            .Select(command => (CommandAst)command);
    }

    private static string? GetOutputVariable(CommandAst command)
    {
        if (command.Parent.Parent is AssignmentStatementAst assignmentStatementAst)
        {
            return assignmentStatementAst.Left.Extent.GetText().TrimStart('$');
        }

        return null;
    }

    private static void GetSkillFunctionNames(CommandElementAst skillFunctionElement, out string skillName, out string functionName)
    {
        var skillFunctionName = skillFunctionElement.Extent.GetText().Split('/').Last();
        var skillFunctionNameParts = skillFunctionName.Split('.');

        skillName = skillFunctionNameParts?.Length > 0 ? skillFunctionNameParts[0] : string.Empty;
        functionName = skillFunctionNameParts?.Length > 1 ? skillFunctionNameParts[1] : skillFunctionName;
    }

    private static Dictionary<string, string> GetVariables(CommandElementAst bodyElement)
    {
        var result = new Dictionary<string, string>();

        if (bodyElement is HashtableAst body)
        {
            foreach (var pair in body.KeyValuePairs)
            {
                var key = pair.Item1.Extent.GetText();
                var value = pair.Item2.Extent.GetText();

                result.Add(key, value);
            }
        }

        return result;
    }

    private static string GetText(this IScriptExtent extent)
    {
        return extent.Text.Replace("\"", string.Empty, StringComparison.Ordinal);
    }

    private const string UriParameterName = "Uri";
    private const string BodyParameterName = "Body";

    #endregion
}

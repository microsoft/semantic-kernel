// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Executes XML plans created by the Function Flow semantic function.
/// </summary>
internal class FunctionFlowRunner
{
    /// <summary>
    /// The tag name used in the plan xml for the user's goal/ask.
    /// </summary>
    internal const string GoalTag = "goal";

    /// <summary>
    /// The tag name used in the plan xml for the solution.
    /// </summary>
    internal const string PlanTag = "plan";

    /// <summary>
    /// The tag name used in the plan xml for a step that calls a skill function.
    /// </summary>
    internal const string FunctionTag = "function.";

    /// <summary>
    /// The tag name used in the plan xml for a conditional check
    /// </summary>
    internal const string ConditionIfTag = "if";

    /// <summary>
    /// The tag name used in the plan xml for a conditional check
    /// </summary>
    internal const string ConditionElseTag = "else";

    /// <summary>
    /// The tag name used in the plan xml for a conditional check
    /// </summary>
    internal const string ConditionWhileTag = "while";

    /// <summary>
    /// The attribute tag used in the plan xml for setting the context variable name to set the output of a function to.
    /// </summary>
    internal const string SetContextVariableTag = "setContextVariable";

    /// <summary>
    /// The attribute tag used in the plan xml for appending the output of a function to the final result for a plan.
    /// </summary>
    internal const string AppendToResultTag = "appendToResult";

    private readonly IKernel _kernel;

    private readonly ConditionalFlowHelper _conditionalFlowHelper;

    public FunctionFlowRunner(IKernel kernel, ITextCompletion? completionBackend = null)
    {
        this._kernel = kernel;
        this._conditionalFlowHelper = new ConditionalFlowHelper(kernel, completionBackend);
    }

    /// <summary>
    /// Executes the next step of a plan xml.
    /// </summary>
    /// <param name="context">The context to execute the plan in.</param>
    /// <param name="planPayload">The plan xml.</param>
    /// <returns>The resulting plan xml after executing a step in the plan.</returns>
    /// <context>
    /// Brief overview of how it works:
    /// 1. The Solution xml is parsed into an XmlDocument.
    /// 2. The Goal node is extracted from the plan xml.
    /// 3. The Plan node is extracted from the plan xml.
    /// 4. The first function node in the plan node is processed.
    /// 5. The resulting plan xml is returned.
    /// </context>
    /// <exception cref="PlanningException">Thrown when the plan xml is invalid.</exception>
    public async Task<SKContext> ExecuteXmlPlanAsync(SKContext context, string planPayload)
    {
        try
        {
            XmlDocument solutionXml = new();
            try
            {
                solutionXml.LoadXml("<xml>" + planPayload + "</xml>");
            }
            catch (XmlException e)
            {
                throw new PlanningException(PlanningException.ErrorCodes.InvalidPlan, "Failed to parse plan xml.", e);
            }

            // Get the Goal
            var (goalTxt, goalXmlString) = GatherGoal(solutionXml);

            // Get the Solution
            XmlNodeList planNodes = solutionXml.GetElementsByTagName(PlanTag);

            // Prepare content for the new plan xml
            var planContent = new StringBuilder();
            _ = planContent.AppendLine($"<{PlanTag}>");

            // Use goal as default function {{INPUT}} -- check and see if it's a plan in Input, if so, use goalTxt, otherwise, use the input.
            if (!context.Variables.Get("PLAN__INPUT", out var planInput))
            {
                // planInput should then be the context.Variables.ToString() only if it's not a plan json
                try
                {
                    var plan = SkillPlan.FromJson(context.Variables.ToString());
                    planInput = string.IsNullOrEmpty(plan.Goal) ? context.Variables.ToString() : goalTxt;
                }
                catch (Exception e) when (!e.IsCriticalException())
                {
                    planInput = context.Variables.ToString();
                }
            }

            string functionInput = string.IsNullOrEmpty(planInput) ? goalTxt : planInput;

            //
            // Process Solution nodes
            //
            context.Log.LogDebug("Processing solution");

            // Process the solution nodes
            string stepResults = await this.ProcessNodeListAsync(planNodes, functionInput, context);
            // Add the solution and variable updates to the new plan xml
            _ = planContent.Append(stepResults)
                .AppendLine($"</{PlanTag}>");
            // Update the plan xml
            var updatedPlan = goalXmlString + planContent.Replace("\r\n", "\n");
            updatedPlan = updatedPlan.Trim();

            context.Variables.Set(SkillPlan.PlanKey, updatedPlan);
            context.Variables.Set("PLAN__INPUT", context.Variables.ToString());

            return context;
        }
        catch (Exception e) when (!e.IsCriticalException())
        {
            context.Log.LogError(e, "Plan execution failed: {0}", e.Message);
            throw;
        }
    }

    private async Task<string> ProcessNodeListAsync(XmlNodeList nodeList, string functionInput, SKContext context)
    {
        var stepAndTextResults = new StringBuilder();
        var processFunctions = true;
        const string INDENT = "  ";
        foreach (XmlNode o in nodeList)
        {
            var parentNodeName = o.Name;
            var ignoreElse = false;
            context.Log.LogTrace("{0}: found node", parentNodeName);
            foreach (XmlNode o2 in o.ChildNodes)
            {
                if (o2.Name == "#text")
                {
                    context.Log.LogTrace("{0}: appending text node", parentNodeName);
                    if (o2.Value != null)
                    {
                        _ = stepAndTextResults.AppendLine(o2.Value.Trim());
                    }

                    continue;
                }

                if (o2.Name.StartsWith(ConditionElseTag, StringComparison.OrdinalIgnoreCase))
                {
                    //If else is the first node throws
                    if (o2.PreviousSibling == null)
                    {
                        throw new PlanningException(PlanningException.ErrorCodes.InvalidPlan, "ELSE tag cannot be the first node in the plan.");
                    }

                    if (ignoreElse)
                    {
                        ignoreElse = false;

                        context.Log.LogTrace("{0}: Skipping processed If's else tag from appending to the plan", parentNodeName);

                        //Continue here will avoid adding this else to the next iteration of the plan
                        continue;
                    }
                }

                if (processFunctions && o2.Name.StartsWith(ConditionWhileTag, StringComparison.OrdinalIgnoreCase))
                {
                    context.Log.LogTrace("{0}: found WHILE tag node", parentNodeName);
                    var whileContent = o2.OuterXml;

                    var functionVariables = context.Variables.Clone();
                    functionVariables.Update(whileContent);

                    var branchWhile = await this._conditionalFlowHelper.WhileAsync(whileContent,
                        new SKContext(functionVariables, this._kernel.Memory, this._kernel.Skills, this._kernel.Log,
                            context.CancellationToken));

                    _ = stepAndTextResults.Append(INDENT).AppendLine(branchWhile);

                    processFunctions = false;

                    // We need to continue so we don't ignore any next siblings to while tag
                    continue;
                }

                if (processFunctions && o2.Name.StartsWith(ConditionIfTag, StringComparison.OrdinalIgnoreCase))
                {
                    context.Log.LogTrace("{0}: found IF tag node", parentNodeName);
                    // Includes IF + ELSE statement
                    var ifFullContent = o2.OuterXml;

                    //Go for the next node to see if it's an else
                    if (this.CheckIfNextNodeIsElseAndGetItsContents(o2, out var elseContents))
                    {
                        ifFullContent += elseContents;

                        // Ignore the next immediate sibling else tag from this IF to the plan since we already processed it
                        ignoreElse = true;
                    }

                    var functionVariables = context.Variables.Clone();
                    functionVariables.Update(ifFullContent);

                    var branchIfOrElse = await this._conditionalFlowHelper.IfAsync(ifFullContent,
                        new SKContext(functionVariables, this._kernel.Memory, this._kernel.Skills, this._kernel.Log,
                            context.CancellationToken));

                    _ = stepAndTextResults.Append(INDENT).AppendLine(branchIfOrElse);

                    processFunctions = false;

                    // We need to continue so we don't ignore any next siblings
                    continue;
                }

                if (o2.Name.StartsWith(FunctionTag, StringComparison.OrdinalIgnoreCase))
                {
                    var splits = o2.Name.SplitEx(FunctionTag);
                    string skillFunctionName = (splits.Length > 1) ? splits[1] : string.Empty;
                    context.Log.LogTrace("{0}: found skill node {1}", parentNodeName, skillFunctionName);
                    GetSkillFunctionNames(skillFunctionName, out var skillName, out var functionName);
                    if (!context.IsFunctionRegistered(skillName, functionName, out var skillFunction))
                    {
                        throw new PlanningException(PlanningException.ErrorCodes.InvalidPlan,
                            $"Plan is using an unavailable skill: {skillName}.{functionName}");
                    }

                    if (processFunctions && !string.IsNullOrEmpty(functionName))
                    {
                        Verify.NotNull(functionName, nameof(functionName));
                        Verify.NotNull(skillFunction, nameof(skillFunction));
                        context.Log.LogTrace("{0}: processing function {1}.{2}", parentNodeName, skillName, functionName);

                        var functionVariables = new ContextVariables(functionInput);
                        var variableTargetName = string.Empty;
                        var appendToResultName = string.Empty;
                        if (o2.Attributes is not null)
                        {
                            foreach (XmlAttribute attr in o2.Attributes)
                            {
                                context.Log.LogTrace("{0}: processing attribute {1}", parentNodeName, attr.ToString());
                                bool innerTextStartWithSign = attr.InnerText.StartsWith("$", StringComparison.Ordinal);

                                if (attr.Name.Equals(SetContextVariableTag, StringComparison.OrdinalIgnoreCase))
                                {
                                    variableTargetName = innerTextStartWithSign
                                        ? attr.InnerText.Substring(1)
                                        : attr.InnerText;
                                }
                                else if (innerTextStartWithSign)
                                {
                                    // Split the attribute value on the comma or ; character
                                    var attrValues = attr.InnerText.Split(new char[] { ',', ';' }, StringSplitOptions.RemoveEmptyEntries);
                                    if (attrValues.Length > 0)
                                    {
                                        // If there are multiple values, create a list of the values
                                        var attrValueList = new List<string>();
                                        foreach (var attrValue in attrValues)
                                        {
                                            if (context.Variables.Get(attrValue.Substring(1), out var variableReplacement))
                                            {
                                                attrValueList.Add(variableReplacement);
                                            }
                                        }

                                        if (attrValueList.Count > 0)
                                        {
                                            functionVariables.Set(attr.Name, string.Concat(attrValueList));
                                        }
                                    }
                                }
                                else if (attr.Name.Equals(AppendToResultTag, StringComparison.OrdinalIgnoreCase))
                                {
                                    appendToResultName = attr.InnerText;
                                }
                                else
                                {
                                    functionVariables.Set(attr.Name, attr.InnerText);
                                }
                            }
                        }

                        // capture current keys before running function
                        var keysToIgnore = functionVariables.Select(x => x.Key).ToList();
                        var result = await this._kernel.RunAsync(functionVariables, skillFunction);
                        // TODO respect ErrorOccurred

                        // copy all values for VariableNames in functionVariables not in keysToIgnore to context.Variables
                        foreach (var variable in functionVariables)
                        {
                            if (!keysToIgnore.Contains(variable.Key, StringComparer.OrdinalIgnoreCase)
                                && functionVariables.Get(variable.Key, out var value))
                            {
                                context.Variables.Set(variable.Key, value);
                            }
                        }

                        _ = context.Variables.Update(result.ToString());
                        if (!string.IsNullOrEmpty(variableTargetName))
                        {
                            context.Variables.Set(variableTargetName, result.ToString());
                        }

                        if (!string.IsNullOrEmpty(appendToResultName))
                        {
                            _ = context.Variables.Get(SkillPlan.ResultKey, out var resultsSoFar);
                            context.Variables.Set(SkillPlan.ResultKey,
                                string.Join(Environment.NewLine + Environment.NewLine, resultsSoFar, appendToResultName, result.ToString()).Trim());
                        }

                        processFunctions = false;
                    }
                    else
                    {
                        context.Log.LogTrace("{0}: appending function node {1}", parentNodeName, skillFunctionName);
                        _ = stepAndTextResults.Append(INDENT).AppendLine(o2.OuterXml);
                    }

                    continue;
                }

                _ = stepAndTextResults.Append(INDENT).AppendLine(o2.OuterXml);
            }
        }

        return stepAndTextResults.Replace("\r\n", "\n").ToString();
    }

    private bool CheckIfNextNodeIsElseAndGetItsContents(XmlNode ifNode, out string? elseContents)
    {
        elseContents = null;
        if (ifNode.NextSibling is null)
        {
            return false;
        }

        if (!ifNode.NextSibling.Name.Equals("else", StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }

        elseContents = ifNode.NextSibling.OuterXml;
        return true;
    }

    private static (string goalTxt, string goalXmlString) GatherGoal(XmlDocument xmlDoc)
    {
        XmlNodeList goal = xmlDoc.GetElementsByTagName(GoalTag);
        if (goal.Count == 0)
        {
            throw new PlanningException(PlanningException.ErrorCodes.InvalidPlan, "No goal found.");
        }

        string goalTxt = goal[0]!.FirstChild!.Value ?? string.Empty;
        var goalContent = new StringBuilder();
        _ = goalContent.Append($"<{GoalTag}>")
            .Append(goalTxt)
            .AppendLine($"</{GoalTag}>");
        return (goalTxt.Trim(), goalContent.Replace("\r\n", "\n").ToString().Trim());
    }

    private static void GetSkillFunctionNames(string skillFunctionName, out string skillName, out string functionName)
    {
        var skillFunctionNameParts = skillFunctionName.Split('.');
        skillName = skillFunctionNameParts?.Length > 0 ? skillFunctionNameParts[0] : string.Empty;
        functionName = skillFunctionNameParts?.Length > 1 ? skillFunctionNameParts[1] : skillFunctionName;
    }
}

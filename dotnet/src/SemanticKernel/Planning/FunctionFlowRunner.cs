// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Orchestration.Extensions;

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
    internal const string SolutionTag = "plan";

    /// <summary>
    /// The tag name used in the plan xml for a step that calls a skill function.
    /// </summary>
    internal const string FunctionTag = "function.";

    /// <summary>
    /// The attribute tag used in the plan xml for setting the context variable name to set the output of a function to.
    /// </summary>
    internal const string SetContextVariableTag = "setContextVariable";

    /// <summary>
    /// The attribute tag used in the plan xml for appending the output of a function to the final result for a plan.
    /// </summary>
    internal const string AppendToResultTag = "appendToResult";

    internal const string OutputTag = "output";

    private readonly IKernel _kernel;

    public FunctionFlowRunner(IKernel kernel)
    {
        this._kernel = kernel;
    }

    /// <summary>
    /// Executes the next step of a plan xml.
    /// </summary>
    /// <param name="context">The context to execute the plan in.</param>
    /// <param name="planPayload">The plan xml.</param>
    /// <returns>The resulting plan xml after executing a step in the plan.</returns>
    /// <context>
    /// Brief overview of how it works:
    /// 1. The plan xml is parsed into an XmlDocument.
    /// 2. The Goal node is extracted from the plan xml.
    /// 3. The Solution node is extracted from the plan xml.
    /// 4. The first function node in the Solution node is processed.
    /// 5. The resulting plan xml is returned.
    /// </context>
    /// <exception cref="PlanningException">Thrown when the plan xml is invalid.</exception>
    public async Task<SKContext> ExecuteXmlPlanAsync(SKContext context, string planPayload)
    {
        try
        {
            XmlDocument xmlDoc = new();
            try
            {
                xmlDoc.LoadXml("<xml>" + planPayload + "</xml>");
            }
            catch (XmlException e)
            {
                throw new PlanningException(PlanningException.ErrorCodes.InvalidPlan, "Failed to parse plan xml.", e);
            }

            // Get the Goal
            var (goalTxt, goalXmlString) = GatherGoal(xmlDoc);

            // Get the Solution
            XmlNodeList solution = xmlDoc.GetElementsByTagName(SolutionTag);

            // Prepare content for the new plan xml
            var solutionContent = new StringBuilder();
            solutionContent.AppendLine($"<{SolutionTag}>");

            // Use goal as default function {{INPUT}} -- check and see if it's a plan in Input, if so, use goalTxt, otherwise, use the input.
            if (!context.Variables.Get("PLAN__INPUT", out var planInput))
            {
                // planInput should then be the context.Variables.ToString() only if it's not a plan json
                try
                {
                    var plan = Plan.FromJson(context.Variables.ToString());
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
            string stepResults = await this.ProcessNodeListAsync(solution, functionInput, context);
            // Add the solution and variable updates to the new plan xml
            solutionContent.Append(stepResults)
                .AppendLine($"</{SolutionTag}>");
            // Update the plan xml
            var updatedPlan = goalXmlString + solutionContent.Replace("\r\n", "\n");
            updatedPlan = updatedPlan.Trim();

            context.Variables.Set(Plan.PlanKey, updatedPlan);
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
            if (o == null)
            {
                continue;
            }

            var parentNodeName = o.Name;

            context.Log.LogTrace("{0}: found node", parentNodeName);
            foreach (XmlNode o2 in o.ChildNodes)
            {
                if (o2.Name == "#text")
                {
                    context.Log.LogTrace("{0}: appending text node", parentNodeName);
                    if (o2.Value != null)
                    {
                        stepAndTextResults.AppendLine(o2.Value.Trim());
                    }

                    continue;
                }

                if (o2.Name.StartsWith(FunctionTag, StringComparison.InvariantCultureIgnoreCase))
                {
                    var skillFunctionName = o2.Name.Split(new string[] { FunctionTag }, StringSplitOptions.None)?[1] ?? string.Empty;
                    context.Log.LogTrace("{0}: found skill node {1}", parentNodeName, skillFunctionName);
                    GetSkillFunctionNames(skillFunctionName, out var skillName, out var functionName);
                    if (processFunctions && !string.IsNullOrEmpty(functionName) && context.IsFunctionRegistered(skillName, functionName, out var skillFunction))
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
                                if (attr.InnerText.StartsWith("$", StringComparison.InvariantCultureIgnoreCase))
                                {
                                    // TODO support lists of parameters like $param1,$param2 or $param1;$param2
                                    if (context.Variables.Get(attr.InnerText.Substring(1), out var variableReplacement))
                                    {
                                        functionVariables.Set(attr.Name, variableReplacement);
                                    }
                                    else if (attr.InnerText.Substring(1).Equals(OutputTag, StringComparison.OrdinalIgnoreCase))
                                    {
                                        // skip
                                    }
                                }
                                else if (attr.Name.Equals(SetContextVariableTag, StringComparison.OrdinalIgnoreCase))
                                {
                                    variableTargetName = attr.InnerText;
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

                        // If skillFunction is BucketOutputsAsync result
                        // we need to pass those things back out to context.Variables
                        if (skillFunctionName.Contains("BucketOutputs"))
                        {
                            // copy all values for VariableNames in functionVariables not in keysToIgnore to context.Variables
                            foreach (KeyValuePair<string, string> kvp in functionVariables)
                            {
                                if (!keysToIgnore.Contains(kvp.Key, StringComparer.InvariantCultureIgnoreCase) && functionVariables.Get(kvp.Key, out var value))
                                {
                                    context.Variables.Set(kvp.Key, value);
                                }
                            }
                        }

                        context.Variables.Update(result.ToString());
                        if (!string.IsNullOrEmpty(variableTargetName))
                        {
                            context.Variables.Set(variableTargetName, result.ToString());
                        }

                        if (!string.IsNullOrEmpty(appendToResultName))
                        {
                            context.Variables.Get(Plan.ResultKey, out var resultsSoFar);
                            context.Variables.Set(Plan.ResultKey,
                                string.Join(Environment.NewLine + Environment.NewLine, resultsSoFar, appendToResultName, result.ToString()));
                        }

                        processFunctions = false;
                    }
                    else
                    {
                        context.Log.LogTrace("{0}: appending function node {1}", parentNodeName, skillFunctionName);
                        stepAndTextResults.Append(INDENT).AppendLine(o2.OuterXml);
                    }

                    continue;
                }

                stepAndTextResults.Append(INDENT).AppendLine(o2.OuterXml);
            }
        }

        return stepAndTextResults.Replace("\r\n", "\n").ToString();
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
        goalContent.Append($"<{GoalTag}>")
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

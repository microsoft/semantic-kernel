// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Xml;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Planning.Sequential;

/// <summary>
/// Parse sequential plan text into a plan.
/// </summary>
internal static class SequentialPlanParser
{
    /// <summary>
    /// The tag name used in the plan xml for the user's goal/ask.
    /// TODO: never used
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

    /// <summary>
    /// The attribute tag used in the plan xml for setting the rationale of the function
    /// </summary>
    internal const string RationaleTag = "rationale";

    /// <summary>
    /// Convert a plan xml string to a plan.
    /// </summary>
    /// <param name="xmlString">The plan xml string.</param>
    /// <param name="goal">The goal for the plan.</param>
    /// <param name="context">The semantic kernel context.</param>
    /// <returns>The plan.</returns>
    /// <exception cref="PlanningException">Thrown when the plan xml is invalid.</exception>
    internal static Plan ToPlanFromXml(this string xmlString, string goal, SKContext context)
    {
        try
        {
            XmlDocument xmlDoc = new();
            try
            {
                xmlDoc.LoadXml("<xml>" + xmlString + "</xml>");
            }
            catch (XmlException e)
            {
                throw new PlanningException(PlanningException.ErrorCodes.InvalidPlan, "Failed to parse plan xml.", e);
            }

            // Get the Solution
            XmlNodeList solution = xmlDoc.GetElementsByTagName(SolutionTag);

            var plan = new Plan(goal);

            // loop through solution node and add to Steps
            foreach (XmlNode solutionNode in solution)
            {
                var parentNodeName = solutionNode.Name;

                foreach (XmlNode childNode in solutionNode.ChildNodes)
                {
                    if (childNode.Name == "#text")
                    {
                        if (childNode.Value != null)
                        {
                            plan.AddSteps(new Plan(childNode.Value.Trim()));
                        }

                        continue;
                    }

                    if (childNode.Name.StartsWith(FunctionTag, StringComparison.OrdinalIgnoreCase))
                    {
                        var skillFunctionName = childNode.Name.Split(s_functionTagArray, StringSplitOptions.None)?[1] ?? string.Empty;
                        GetSkillFunctionNames(skillFunctionName, out var skillName, out var functionName);

                        if (!string.IsNullOrEmpty(functionName) && context.Skills!.TryGetFunction(skillName, functionName, out var skillFunction))
                        {
                            var planStep = new Plan(skillFunction);

                            var functionVariables = new ContextVariables();
                            var functionOutputs = new List<string>();
                            var functionResults = new List<string>();

                            var view = skillFunction.Describe();
                            foreach (var p in view.Parameters)
                            {
                                functionVariables.Set(p.Name, p.DefaultValue);
                            }

                            if (childNode.Attributes is not null)
                            {
                                foreach (XmlAttribute attr in childNode.Attributes)
                                {
                                    context.Log.LogTrace("{0}: processing attribute {1}", parentNodeName, attr.ToString());
                                    if (attr.Name.Equals(SetContextVariableTag, StringComparison.OrdinalIgnoreCase))
                                    {
                                        functionOutputs.Add(attr.InnerText);
                                    }
                                    else if (attr.Name.Equals(RationaleTag, StringComparison.OrdinalIgnoreCase))
                                    {
                                        planStep.Rationale = attr.InnerText;
                                    }
                                    else if (attr.Name.Equals(AppendToResultTag, StringComparison.OrdinalIgnoreCase))
                                    {
                                        functionOutputs.Add(attr.InnerText);
                                        functionResults.Add(attr.InnerText);
                                    }
                                    else
                                    {
                                        functionVariables.Set(attr.Name, attr.InnerText);
                                    }
                                }
                            }

                            // Plan properties
                            planStep.Outputs = functionOutputs;
                            planStep.Parameters = functionVariables;
                            foreach (var result in functionResults)
                            {
                                plan.Outputs.Add(result);
                            }

                            plan.AddSteps(planStep);
                        }
                        else
                        {
                            context.Log.LogTrace("{0}: appending function node {1}", parentNodeName, skillFunctionName);
                            plan.AddSteps(new Plan(childNode.InnerText));
                        }

                        continue;
                    }

                    plan.AddSteps(new Plan(childNode.InnerText));
                }
            }

            return plan;
        }
        catch (Exception e) when (!e.IsCriticalException())
        {
            context.Log.LogError(e, "Plan parsing failed: {0}", e.Message);
            throw;
        }
    }

    private static void GetSkillFunctionNames(string skillFunctionName, out string skillName, out string functionName)
    {
        var skillFunctionNameParts = skillFunctionName.Split('.');
        skillName = skillFunctionNameParts?.Length > 0 ? skillFunctionNameParts[0] : string.Empty;
        functionName = skillFunctionNameParts?.Length > 1 ? skillFunctionNameParts[1] : skillFunctionName;
    }

    private static readonly string[] s_functionTagArray = new string[] { FunctionTag };
}

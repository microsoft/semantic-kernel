// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text;
using System.Threading.Tasks;
using System.Xml;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Executes plans created by the PlannerSkill/ProblemSolver semantic function.
/// </summary>
internal class PlanRunner
{
    /// <summary>
    /// The tag name used in the plan xml for the user's goal/ask.
    /// </summary>
    private const string GoalTag = "goal";

    /// <summary>
    /// The tag name used in the plan xml for the solution.
    /// </summary>
    private const string SolutionTag = "solution";

    /// <summary>
    /// The tag name used in the plan xml for a generic step.
    /// </summary>
    private const string StepTag = "step";

    /// <summary>
    /// The tag name used in the plan xml for the context variables.
    /// </summary>
    private const string VariablesTag = "variables";

    private readonly IKernel _kernel;

    public PlanRunner(IKernel kernel)
    {
        this._kernel = kernel;
    }

    /// <summary>
    /// Executes the next step of a plan xml.
    /// </summary>
    /// <param name="context">The context to execute the plan in.</param>
    /// <param name="planPayload">The plan xml.</param>
    /// <param name="defaultStepExecutor">The default step executor to use if a step does not have a skill function.</param>
    /// <returns>The resulting plan xml after executing a step in the plan.</returns>
    /// <context>
    /// Brief overview of how it works:
    /// 1. The plan xml is parsed into a list of goals, variables, arguments, and steps.
    /// 2. The first step is executed.
    /// 3. The resulting context is converted into a new plan xml.
    /// 4. The new plan xml is returned.
    /// </context>
    /// <exception cref="PlanningException">Thrown when the plan xml is invalid.</exception>
    public async Task<SKContext> ExecuteXmlPlanAsync(SKContext context, string planPayload, ISKFunction defaultStepExecutor)
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
            var (_, goalXmlString) = GatherGoal(xmlDoc);

            // Get the <see cref="ContextVariables"/> and Solution
            XmlNodeList variables = xmlDoc.GetElementsByTagName(VariablesTag);
            XmlNodeList solution = xmlDoc.GetElementsByTagName(SolutionTag);

            // Prepare content for the new plan xml
            var variablesContent = new StringBuilder();
            var solutionContent = new StringBuilder();
            variablesContent.AppendLine($"<{VariablesTag}>");
            solutionContent.AppendLine($"<{SolutionTag}>");

            //
            //Process <see cref="ContextVariables"/> nodes
            //
            context.Log.LogDebug("Processing context variables");
            // Process the context variables nodes
            var stepResults = this.ProcessNodeList(variables, context);
            // Add the context variables to the new plan xml
            variablesContent.Append(stepResults)
                .AppendLine($"</{VariablesTag}>");

            //
            // Process Solution nodes
            //
            context.Log.LogDebug("Processing solution");

            // Process the solution nodes
            stepResults = this.ProcessNodeList(solution, context);
            // Add the solution and context variables updates to the new plan xml
            solutionContent.Append(stepResults)
                .AppendLine($"</{SolutionTag}>");

            // Update the plan xml
            var updatedPlan = goalXmlString + variablesContent + solutionContent;
            updatedPlan = updatedPlan.Trim();
            context.Variables.Update(updatedPlan);

            // Otherwise, execute the next step in the plan
            var nextPlan = (await this._kernel.RunAsync(context.Variables, defaultStepExecutor)).ToString().Trim();

            // And return the updated context with the updated plan xml
            context.Variables.Update(nextPlan);
            return context;
        }
        catch (Exception e) when (!e.IsCriticalException())
        {
            context.Log.LogError(e, "Plan execution failed: {0}", e.Message);
            throw;
        }
    }

    private string ProcessNodeList(XmlNodeList nodeList, SKContext context)
    {
        var stepAndTextResults = new StringBuilder();
        const string INDENT = "  ";
        if (nodeList != null)
        {
            foreach (XmlNode o in nodeList)
            {
                if (o == null)
                {
                    continue;
                }

                var parentNodeName = o.Name;

                context.Log.LogDebug("{0}: found node", parentNodeName);
                foreach (XmlNode o2 in o.ChildNodes)
                {
                    if (o2.Name == "#text")
                    {
                        context.Log.LogDebug("{0}: appending text node", parentNodeName);
                        stepAndTextResults.AppendLine(o2.Value.Trim());
                        continue;
                    }

                    if (o2.Name == StepTag)
                    {
                        context.Log.LogDebug("{0}: appending step node {1}", parentNodeName, o2.OuterXml);
                        stepAndTextResults.Append(INDENT).AppendLine(o2.OuterXml);
                        continue;
                    }

                    stepAndTextResults.Append(INDENT).AppendLine(o2.OuterXml);
                }
            }
        }

        return stepAndTextResults.ToString();
    }

    // TODO: goalTxt is never used
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
        return (goalTxt, goalContent.ToString());
    }
}

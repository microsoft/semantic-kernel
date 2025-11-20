// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text;

namespace Microsoft.SemanticKernel.Process.Tools;

/// <summary>
/// Provides extension methods to visualize a process as a Mermaid diagram.
/// </summary>
public static class ProcessVisualizationExtensions
{
    /// <summary>
    /// Generates a Mermaid diagram from a process builder.
    /// </summary>
    /// <param name="processBuilder"></param>
    /// <param name="maxLevel">The maximum indentation level to reach for nested processes, 1 is basically no nesting</param>
    /// <returns></returns>
    public static string ToMermaid(this ProcessBuilder processBuilder, int maxLevel = 2)
    {
        var process = processBuilder.Build();
        return process.ToMermaid(maxLevel);
    }

    /// <summary>
    /// Generates a Mermaid diagram from a kernel process.
    /// </summary>
    /// <param name="process"></param>
    /// <param name="maxLevel">The maximum indentation level to reach for nested processes, 1 is basically no nesting</param>
    /// <returns></returns>
    public static string ToMermaid(this KernelProcess process, int maxLevel = 2)
    {
        // Check that the maximum level is at least 1
        if (maxLevel < 1)
        {
            throw new InvalidOperationException("The maximum indentation level must be at least 1.");
        }

        StringBuilder sb = new();
        sb.AppendLine("flowchart LR");

        // Generate the Mermaid flowchart content with indentation
        string flowchartContent = RenderProcess(process, 1, isSubProcess: false, maxLevel);

        // Append the formatted content to the main StringBuilder
        sb.Append(flowchartContent);

        return sb.ToString();
    }

    /// <summary>
    /// Renders a process and its nested processes recursively as a Mermaid flowchart.
    /// </summary>
    /// <param name="process">The process to render.</param>
    /// <param name="level">The indentation level for nested processes.</param>
    /// <param name="isSubProcess">Indicates if the current process is a sub-process.</param>
    /// <param name="maxLevel">The maximum indentation level to reach for nested processes, 1 is basically no nesting</param>
    /// <returns>A string representation of the process in Mermaid syntax.</returns>
    private static string RenderProcess(KernelProcess process, int level, bool isSubProcess, int maxLevel = 2)
    {
        StringBuilder sb = new();
        string indentation = new(' ', 4 * level);

        // Dictionary to map step IDs to step names
        var stepNames = process.Steps
            .Where(step => step.State.RunId != null && step.State.StepId != null)
            .ToDictionary(
                step => step.State.RunId!,
                step => step.State.StepId!
            );

        // Add Start and End nodes only if this is not a sub-process
        if (!isSubProcess)
        {
            sb.AppendLine($"{indentation}Start[\"Start\"]");
            sb.AppendLine($"{indentation}End[\"End\"]");
        }

        // Process each step
        foreach (var step in process.Steps)
        {
            var stepId = step.State.RunId;
            var stepName = step.State.StepId;

            // Check if the step is a nested process (sub-process)
            if (step is KernelProcess nestedProcess && level < maxLevel)
            {
                sb.AppendLine($"{indentation}subgraph {stepName.Replace(" ", "")}[\"{stepName}\"]");
                sb.AppendLine($"{indentation}    direction LR");

                // Render the nested process content without its own Start/End nodes
                string nestedFlowchart = RenderProcess(nestedProcess, level + 1, isSubProcess: true, maxLevel);

                sb.Append(nestedFlowchart);
                sb.AppendLine($"{indentation}end");
            }
            else if (step is KernelProcess nestedProcess2 && level >= maxLevel)
            {
                // Render a subprocess step
                sb.AppendLine($"{indentation}{stepName}[[\"{stepName}\"]]");
            }
            else
            {
                // Render the regular step
                sb.AppendLine($"{indentation}{stepName}[\"{stepName}\"]");
            }

            // Handle edges from this step
            if (step.Edges != null)
            {
                foreach (var kvp in step.Edges)
                {
                    var eventId = kvp.Key;
                    var stepEdges = kvp.Value;

                    // Skip drawing edges that point to a nested process as an entry point
                    if (stepNames.ContainsKey(eventId) && process.Steps.Any(s => s.State.StepId == eventId && s is KernelProcess))
                    {
                        continue;
                    }

                    foreach (var edge in stepEdges)
                    {
                        string source = $"{stepName}[\"{stepName}\"]";
                        string target;

                        if (edge.OutputTarget is KernelProcessFunctionTarget functionTarget)
                        {
                            // Check if the target step is the end node by function name
                            if (functionTarget.FunctionName.Equals("end", StringComparison.OrdinalIgnoreCase) && !isSubProcess)
                            {
                                target = "End[\"End\"]";
                            }
                            else if (stepNames.TryGetValue(functionTarget.StepId, out string? targetStepName))
                            {
                                target = $"{targetStepName}[\"{targetStepName}\"]";
                            }
                            else
                            {
                                // Handle cases where the target step is not in the current dictionary, possibly a nested step or placeholder
                                // As we have events from the step that, when it is a subprocess, that go to a step in the subprocess
                                // Those are triggered by events and do not have an origin step, also they are not connected to the Start node
                                // So we need to handle them separately - we ignore them for now
                                continue;
                            }

                            // Append the connection
                            sb.AppendLine($"{indentation}{source} --> {target}");
                        }
                    }
                }
            }
        }

        // Connect Start to the first step and the last step to End (only for the main process)
        if (!isSubProcess && process.Steps.Count > 0)
        {
            var firstStepName = process.Steps.First().State.StepId;
            var lastStepName = process.Steps.Last().State.StepId;

            sb.AppendLine($"{indentation}Start --> {firstStepName}[\"{firstStepName}\"]");
            sb.AppendLine($"{indentation}{lastStepName}[\"{lastStepName}\"] --> End");
        }

        return sb.ToString();
    }
}

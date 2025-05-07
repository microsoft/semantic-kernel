// Copyright (c) Microsoft. All rights reserved.

using System.Linq;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Export a process to a string representation.
/// </summary>
public sealed class ProcessExporter
{
    /// <summary>
    /// Export a process to a string representation.
    /// </summary>
    /// <param name="process"></param>
    /// <returns></returns>
    public static string ExportProcess(KernelProcess process)
    {
        Verify.NotNull(process);

        Workflow workflow = new()
        {
            Name = process.State.Name,
            Description = process.Description,
            FormatVersion = "1.0",
            WorkflowVersion = process.State.Version,
            Nodes = [.. process.Steps.Select(step => GetNodeFromStep(step))],
            // Orchestration
            // Suggested Inputs
            // Variables
            // Schema
            // Error handling
        };

        return "";
    }

    private static Node GetNodeFromStep(KernelProcessStepInfo stepInfo)
    {
        Verify.NotNull(stepInfo);

        if (stepInfo is KernelProcess)
        {
            throw new KernelException("Processes that contain a subprocess are not currently exportable.");
        }
        else if (stepInfo is KernelProcessAgentStep agentStep)
        {
            var agentNode = new Node()
            {
                Id = agentStep.State.Id ?? throw new KernelException("All steps must have an Id."),
                Description = agentStep.Description,
                Type = "agent",
                Inputs = agentStep.Inputs,
                OnComplete = null, // TODO: OnComplete,
                OnError = null // TODO: OnError
            };
        }
        else if (stepInfo is KernelProcessMap mapStep)
        {
            throw new KernelException("Processes that contain a map step are not currently exportable.");
        }
        else if (stepInfo is KernelProcessProxy proxyStep)
        {
            throw new KernelException("Processes that contain a proxy step are not currently exportable.");
        }
        else
        {
            throw new KernelException("Processes that contain non Foundry-Agent step are not currently exportable.");
        }

        return new Node();
    }
}

// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Agents.OpenAI.Extensions;

internal static class KernelExtensions
{
    /// <summary>
    /// Retrieve a kernel function based on the tool name.
    /// </summary>
    public static KernelFunction GetAssistantTool(this Kernel kernel, string toolName, char delimiter)
    {
        string[] nameParts = toolName.Split(delimiter);
        return nameParts.Length switch
        {
            2 => kernel.Plugins.GetFunction(nameParts[0], nameParts[1]),
            _ => throw new KernelException($"Agent Failure - Unknown tool: {toolName}"),
        };
    }
}

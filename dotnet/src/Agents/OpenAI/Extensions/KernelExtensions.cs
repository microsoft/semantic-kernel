// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Agents.Extensions;

internal static class KernelExtensions
{
    /// <summary>
    /// Retrieve a kernel function based on the tool name.
    /// </summary>
    public static KernelFunction GetAssistantTool(this Kernel kernel, string toolName, char delimeter)
    {
        string[] nameParts = toolName.Split(delimeter);
        return nameParts.Length switch
        {
            2 => kernel.Plugins.GetFunction(nameParts[0], nameParts[1]),
            _ => throw new KernelException($"Unknown tool: {toolName}"),
        };
    }
}

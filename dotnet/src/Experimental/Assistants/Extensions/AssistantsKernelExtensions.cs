// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Experimental.Assistants.Exceptions;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

internal static class AssistantsKernelExtensions
{
    /// <summary>
    /// Retrieve a kernel function based on the tool name.
    /// </summary>
    public static KernelFunction GetAssistantTool(this Kernel kernel, string toolName)
    {
        string[] nameParts = toolName.Split('-');
        return nameParts.Length switch
        {
            2 => kernel.Plugins.GetFunction(nameParts[0], nameParts[1]),
            _ => throw new AssistantException($"Unknown tool: {toolName}"),
        };
    }
}

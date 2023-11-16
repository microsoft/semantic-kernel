// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Experimental.Assistants.Extensions;

internal static class IKernelExtensions
{
    /// <summary>
    /// Retrieve a kernel function based on the tool name.
    /// </summary>
    public static ISKFunction GetAssistantTool(this IKernel kernel, string toolName)
    {
        string[] nameParts = toolName.Split('-');
        return nameParts.Length switch
        {
            1 => kernel.Functions.GetFunction(toolName),
            2 => kernel.Functions.GetFunction(nameParts[0], nameParts[1]),
            _ => throw new SKException($"Unknown tool: {toolName}"),
        };
    }
}

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
        switch (nameParts.Length)
        {
            case 1:
                return kernel.Functions.GetFunction(toolName);
            case 2:
                return kernel.Functions.GetFunction(nameParts[0], nameParts[1]);
            default:
                throw new SKException($"Unknown tool: {toolName}");
        }
    }
}

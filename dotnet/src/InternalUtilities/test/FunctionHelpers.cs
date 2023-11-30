// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;

namespace SemanticKernel.UnitTests;

/// <summary>Test helpers for working with native functions.</summary>
internal static class FunctionHelpers
{
    /// <summary>
    /// Invokes a function on a plugin instance via the kernel.
    /// </summary>
    public static Task<FunctionResult> CallViaKernelAsync(
        object pluginInstance,
        string methodName,
        params (string Name, object Value)[] variables)
    {
        var kernel = new Kernel();

        IKernelPlugin plugin = kernel.ImportPluginFromObject(pluginInstance);

        KernelArguments arguments = new();

        foreach ((string Name, object Value) pair in variables)
        {
            arguments[pair.Name] = pair.Value?.ToString() ?? string.Empty;
        }

        return kernel.InvokeAsync(plugin[methodName], arguments);
    }
}

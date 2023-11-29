// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Orchestration;

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

        ContextVariables contextVariables = new();

        foreach ((string Name, object Value) pair in variables)
        {
            contextVariables.Set(pair.Name, pair.Value.ToString());
        }

        return kernel.InvokeAsync(plugin[methodName], contextVariables);
    }
}

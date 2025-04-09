// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using Microsoft.SemanticKernel.Connectors.MistralAI.Client;

namespace Microsoft.SemanticKernel.Connectors.MistralAI;

/// <summary>
/// Extension methods for <see cref="IReadOnlyKernelPluginCollection"/>.
/// </summary>
internal static class MistralAIPluginCollectionExtensions
{
    /// <summary>
    /// Given an <see cref="MistralFunction"/> object, tries to retrieve the corresponding <see cref="KernelFunction"/> and populate <see cref="KernelArguments"/> with its parameters.
    /// </summary>
    /// <param name="plugins">The plugins.</param>
    /// <param name="functionToolCall">The <see cref="MistralFunction"/> object.</param>
    /// <param name="function">When this method returns, the function that was retrieved if one with the specified name was found; otherwise, <see langword="null"/></param>
    /// <param name="arguments">When this method returns, the arguments for the function; otherwise, <see langword="null"/></param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    internal static bool TryGetFunctionAndArguments(
        this IReadOnlyKernelPluginCollection plugins,
        MistralFunction functionToolCall,
        [NotNullWhen(true)] out KernelFunction? function,
        out KernelArguments? arguments)
    {
        if (plugins.TryGetFunction(functionToolCall.PluginName, functionToolCall.FunctionName, out function))
        {
            // Add parameters to arguments
            arguments = null;
            if (functionToolCall.Arguments is not null)
            {
                // TODO user serializer options from the Kernel
                var functionArguments = JsonSerializer.Deserialize<Dictionary<string, object>>(functionToolCall.Arguments);
                // TODO record error if deserialization fails

                if (functionArguments is not null)
                {
                    arguments = [];

                    foreach (var key in functionArguments.Keys)
                    {
                        arguments[key] = functionArguments[key];
                    }
                }
            }

            return true;
        }

        // Function not found in collection
        arguments = null;
        return false;
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json;

namespace Microsoft.SemanticKernel.Connectors.Google.Core;

/// <summary>
/// Extension methods for <see cref="IReadOnlyKernelPluginCollection"/>.
/// </summary>
internal static class GeminiPluginCollectionExtensions
{
    /// <summary>
    /// Given an <see cref="GeminiFunctionToolCall"/> object, tries to retrieve the corresponding <see cref="KernelFunction"/>
    /// and populate <see cref="KernelArguments"/> with its parameters.
    /// </summary>
    /// <param name="plugins">The plugins.</param>
    /// <param name="functionToolCall">The <see cref="GeminiFunctionToolCall"/> object.</param>
    /// <param name="function">When this method returns, the function that was retrieved
    /// if one with the specified name was found; otherwise, <see langword="null"/></param>
    /// <param name="arguments">When this method returns, the arguments for the function; otherwise, <see langword="null"/></param>
    /// <returns><see langword="true"/> if the function was found; otherwise, <see langword="false"/>.</returns>
    public static bool TryGetFunctionAndArguments(
        this IReadOnlyKernelPluginCollection plugins,
        GeminiFunctionToolCall functionToolCall,
        [NotNullWhen(true)] out KernelFunction? function,
        out KernelArguments? arguments)
    {
        if (plugins.TryGetFunction(functionToolCall.PluginName, functionToolCall.FunctionName, out function))
        {
            // Add parameters to arguments
            arguments = null;
            if (functionToolCall.Arguments is not null)
            {
                arguments = [];
                foreach (var parameter in functionToolCall.Arguments)
                {
                    // Check if the parameter.Value is a JsonElement and create a switch expression to handle different types
                    arguments[parameter.Key] = parameter.Value switch
                    {
                        JsonElement jsonElement => jsonElement.ValueKind switch
                        {
                            JsonValueKind.String => jsonElement.GetString(),
                            JsonValueKind.Number => jsonElement.TryGetInt32(out int intValue) ? intValue :
                                                                  jsonElement.TryGetInt64(out long longValue) ? longValue :
                                                                  jsonElement.TryGetDouble(out double doubleValue) ? doubleValue :
                                                                  jsonElement.GetRawText(),
                            JsonValueKind.True => true,
                            JsonValueKind.False => false,
                            JsonValueKind.Null => null,
                            // For arrays and objects, return the raw JSON which can be parsed by the function implementation
                            _ => jsonElement.GetRawText()
                        },
                        _ => parameter.Value?.ToString()
                    };
                }
            }

            return true;
        }

        // Function not found in collection
        arguments = null;
        return false;
    }
}

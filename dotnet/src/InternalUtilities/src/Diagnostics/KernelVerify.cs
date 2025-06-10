// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Text.RegularExpressions;

namespace Microsoft.SemanticKernel;

[ExcludeFromCodeCoverage]
internal static partial class KernelVerify
{
#if NET
    [GeneratedRegex("^[0-9A-Za-z_]*$")]
    private static partial Regex AllowedPluginNameSymbolsRegex();

    [GeneratedRegex("^[0-9A-Za-z_-]*$")]
    private static partial Regex AllowedFunctionNameSymbolsRegex();
#else
    private static Regex AllowedPluginNameSymbolsRegex() => s_allowedPluginNameSymbolsRegex;
    private static readonly Regex s_allowedPluginNameSymbolsRegex = new("^[0-9A-Za-z_]*$", RegexOptions.Compiled);

    private static Regex AllowedFunctionNameSymbolsRegex() => s_allowedFunctionNameSymbolsRegex;
    private static readonly Regex s_allowedFunctionNameSymbolsRegex = new("^[0-9A-Za-z_-]*$", RegexOptions.Compiled);
#endif

    internal static void ValidPluginName([NotNull] string? pluginName, IReadOnlyKernelPluginCollection? plugins = null, [CallerArgumentExpression(nameof(pluginName))] string? paramName = null)
    {
        Verify.NotNullOrWhiteSpace(pluginName);
        if (!AllowedPluginNameSymbolsRegex().IsMatch(pluginName))
        {
            Verify.ThrowArgumentInvalidName("plugin name", pluginName, paramName);
        }

        if (plugins is not null && plugins.Contains(pluginName))
        {
            throw new ArgumentException($"A plugin with the name '{pluginName}' already exists.");
        }
    }

    internal static void ValidFunctionName([NotNull] string? functionName, [CallerArgumentExpression(nameof(functionName))] string? paramName = null)
    {
        Verify.NotNullOrWhiteSpace(functionName);
        if (!AllowedFunctionNameSymbolsRegex().IsMatch(functionName))
        {
            Verify.ThrowArgumentInvalidName("function name", functionName, paramName);
        }
    }

    /// <summary>
    /// Make sure every function parameter name is unique
    /// </summary>
    /// <param name="parameters">List of parameters</param>
    internal static IReadOnlyList<KernelParameterMetadata> ParametersUniqueness(IReadOnlyList<KernelParameterMetadata> parameters)
    {
        int count = parameters.Count;
        if (count > 0)
        {
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            for (int i = 0; i < count; i++)
            {
                KernelParameterMetadata p = parameters[i];
                if (string.IsNullOrWhiteSpace(p.Name))
                {
                    string paramName = $"{nameof(parameters)}[{i}].{p.Name}";
                    if (p.Name is null)
                    {
                        Verify.ThrowArgumentNullException(paramName);
                    }
                    else
                    {
                        Verify.ThrowArgumentWhiteSpaceException(paramName);
                    }
                }

                if (!seen.Add(p.Name))
                {
                    throw new ArgumentException($"The function has two or more parameters with the same name '{p.Name}'");
                }
            }
        }

        return parameters;
    }
}

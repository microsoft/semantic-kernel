// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;

namespace Microsoft.SemanticKernel;

// This file contains Verify methods which depend on Semantic Kernel APIs.

internal static partial class Verify
{
    internal static void ValidPluginName([NotNull] string? pluginName, IReadOnlyKernelPluginCollection? plugins = null, [CallerArgumentExpression(nameof(pluginName))] string? paramName = null)
    {
        NotNullOrWhiteSpace(pluginName);
        if (!AsciiLettersDigitsUnderscoresRegex().IsMatch(pluginName))
        {
            ThrowArgumentInvalidName("plugin name", pluginName, paramName);
        }

        if (plugins is not null && plugins.Contains(pluginName))
        {
            throw new ArgumentException($"A plugin with the name '{pluginName}' already exists.");
        }
    }

    /// <summary>
    /// Make sure every function parameter name is unique
    /// </summary>
    /// <param name="parameters">List of parameters</param>
    internal static void ParametersUniqueness(IReadOnlyList<KernelParameterMetadata> parameters)
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
                        ThrowArgumentNullException(paramName);
                    }
                    else
                    {
                        ThrowArgumentWhiteSpaceException(paramName);
                    }
                }

                if (!seen.Add(p.Name))
                {
                    throw new ArgumentException($"The function has two or more parameters with the same name '{p.Name}'");
                }
            }
        }
    }
}

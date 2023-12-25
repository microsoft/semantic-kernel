// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Runtime.CompilerServices;
using System.Text.RegularExpressions;

namespace Microsoft.SemanticKernel;

internal static partial class Verify
{
#if NET8_0_OR_GREATER
    [GeneratedRegex("^[0-9A-Za-z_]*$")]
    internal static partial Regex AsciiLettersDigitsUnderscoreRegex();

    [GeneratedRegex("^[0-9A-Za-z_.]*$")]
    internal static partial Regex AsciiLettersDigitsUnderscorePeriodRegex();
#else
    private static readonly Regex s_asciiLettersDigitsUnderscoreRegex = new("^[0-9A-Za-z_]*$");
    internal static Regex AsciiLettersDigitsUnderscoreRegex() => s_asciiLettersDigitsUnderscoreRegex;

    private static readonly Regex s_asciiLettersDigitsUnderscorePeriodRegex = new("^[0-9A-Za-z_.]*$");
    internal static Regex AsciiLettersDigitsUnderscorePeriodRegex() => s_asciiLettersDigitsUnderscorePeriodRegex;
#endif

    /// <summary>
    /// Equivalent of ArgumentNullException.ThrowIfNull
    /// </summary>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void NotNull([NotNull] object? obj, [CallerArgumentExpression("obj")] string? paramName = null)
    {
        if (obj is null)
        {
            ThrowArgumentNullException(paramName);
        }
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void NotNullOrWhiteSpace([NotNull] string? str, [CallerArgumentExpression("str")] string? paramName = null)
    {
        NotNull(str, paramName);
        if (string.IsNullOrWhiteSpace(str))
        {
            ThrowArgumentWhiteSpaceException(paramName);
        }
    }

    internal static void NotNullOrEmpty<T>(IList<T> list, [CallerArgumentExpression("list")] string? paramName = null)
    {
        NotNull(list, paramName);
        if (list.Count == 0)
        {
            throw new ArgumentException("The value cannot be empty.", paramName);
        }
    }

    public static void True(bool condition, string message, [CallerArgumentExpression("condition")] string? paramName = null)
    {
        if (!condition)
        {
            throw new ArgumentException(message, paramName);
        }
    }

    internal static void ValidPluginName([NotNull] string? pluginName, IReadOnlyKernelPluginCollection? plugins = null, [CallerArgumentExpression("pluginName")] string? paramName = null)
    {
        NotNullOrWhiteSpace(pluginName);
        if (!AsciiLettersDigitsUnderscoreRegex().IsMatch(pluginName))
        {
            ThrowArgumentInvalidName("plugin name", pluginName, paramName);
        }

        if (plugins is not null && plugins.Contains(pluginName))
        {
            throw new ArgumentException($"A plugin with the name '{pluginName}' already exists.");
        }
    }

    internal static void ValidFunctionName([NotNull] string? functionName, [CallerArgumentExpression("functionName")] string? paramName = null)
    {
        NotNullOrWhiteSpace(functionName);
        if (!AsciiLettersDigitsUnderscoreRegex().IsMatch(functionName))
        {
            ThrowArgumentInvalidName("function name", functionName, paramName);
        }
    }

    internal static void ValidParameterName(string name, int index)
    {
        if (string.IsNullOrWhiteSpace(name))
        {
            string paramName = $"parameters[{index}].{name}";
            if (name is null)
            {
                ThrowArgumentNullException(paramName);
            }
            else
            {
                ThrowArgumentWhiteSpaceException(paramName);
            }
        }
    }

    public static void ValidateUrl(string url, bool allowQuery = false, [CallerArgumentExpression("url")] string? paramName = null)
    {
        NotNullOrWhiteSpace(url, paramName);

        if (!Uri.TryCreate(url, UriKind.Absolute, out var uri) || string.IsNullOrEmpty(uri.Host))
        {
            throw new ArgumentException($"The `{url}` is not valid.", paramName);
        }

        if (!allowQuery && !string.IsNullOrEmpty(uri.Query))
        {
            throw new ArgumentException($"The `{url}` is not valid: it cannot contain query parameters.", paramName);
        }

        if (!string.IsNullOrEmpty(uri.Fragment))
        {
            throw new ArgumentException($"The `{url}` is not valid: it cannot contain URL fragments.", paramName);
        }
    }

    internal static void StartsWith(string text, string prefix, string message, [CallerArgumentExpression("text")] string? textParamName = null)
    {
        Debug.Assert(prefix is not null);

        NotNullOrWhiteSpace(text, textParamName);
        if (!text.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
        {
            throw new ArgumentException(textParamName, message);
        }
    }

    internal static void DirectoryExists(string path)
    {
        if (!Directory.Exists(path))
        {
            throw new DirectoryNotFoundException($"Directory '{path}' could not be found.");
        }
    }

    /// <summary>
    /// Make sure every function parameter name is unique
    /// </summary>
    /// <param name="parameters">List of parameters</param>
    internal static void ParametersUniqueness(IReadOnlyList<KernelParameterMetadata> parameters)
    {
        // Functions with a small number of parameters are most common, and we can avoid
        // the overhead of a hashset for those cases.
        int count = parameters.Count;
        switch (count)
        {
            case 0:
                // Nothing to validate.
                break;

            case 1:
                // A single parameter is always unique.
                ValidParameterName(parameters[0].Name, 0);
                break;

            case 2:
                // Two parameters are unique if they have different names.
                string first = parameters[0].Name, second = parameters[1].Name;
                ValidParameterName(first, 0);
                ValidParameterName(second, 1);
                if (first.Equals(second, StringComparison.OrdinalIgnoreCase))
                {
                    ThrowArgumentNotUnique(parameters[0].Name);
                }
                break;

            default:
                // For anything more use a hashset to check for uniqueness.
                var seen = new HashSet<string>(
#if NET6_0_OR_GREATER
                    count,
#endif
                    StringComparer.OrdinalIgnoreCase);
                for (int i = 0; i < count; i++)
                {
                    KernelParameterMetadata p = parameters[i];
                    ValidParameterName(p.Name, i);
                    if (!seen.Add(p.Name))
                    {
                        ThrowArgumentNotUnique(p.Name);
                    }
                }
                break;
        }
    }

    [DoesNotReturn]
    private static void ThrowArgumentNotUnique(string name) =>
        throw new ArgumentException($"The function has two or more parameters with the same name '{name}'");

    [DoesNotReturn]
    private static void ThrowArgumentInvalidName(string kind, string name, string? paramName) =>
        throw new ArgumentException($"A {kind} can contain only ASCII letters, digits, and underscores: '{name}' is not a valid name.", paramName);

    [DoesNotReturn]
    internal static void ThrowArgumentNullException(string? paramName) =>
        throw new ArgumentNullException(paramName);

    [DoesNotReturn]
    internal static void ThrowArgumentWhiteSpaceException(string? paramName) =>
        throw new ArgumentException("The value cannot be an empty string or composed entirely of whitespace.", paramName);
}

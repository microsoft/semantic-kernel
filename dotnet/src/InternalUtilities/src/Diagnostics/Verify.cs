// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Runtime.CompilerServices;
using System.Text.RegularExpressions;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Diagnostics;

internal static class Verify
{
    private static readonly Regex s_asciiLettersDigitsUnderscoresRegex = new("^[0-9A-Za-z_]*$");

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

    internal static void ValidSkillName([NotNull] string? skillName)
    {
        NotNullOrWhiteSpace(skillName);
        if (!s_asciiLettersDigitsUnderscoresRegex.IsMatch(skillName))
        {
            ThrowInvalidName("skill name", skillName);
        }
    }

    internal static void ValidFunctionName([NotNull] string? functionName) =>
        ValidName(functionName, "function name");

    internal static void ValidFunctionParamName([NotNull] string? functionParamName) =>
        ValidName(functionParamName, "function parameter name");

    private static void ValidName([NotNull] string? name, string kind)
    {
        NotNullOrWhiteSpace(name);
        if (!s_asciiLettersDigitsUnderscoresRegex.IsMatch(name))
        {
            ThrowInvalidName(kind, name);
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
    internal static void ParametersUniqueness(IList<ParameterView> parameters)
    {
        int count = parameters.Count;
        if (count > 0)
        {
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            for (int i = 0; i < count; i++)
            {
                ParameterView p = parameters[i];
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
                    throw new SKException($"The function has two or more parameters with the same name '{p.Name}'");
                }
            }
        }
    }

    /// <summary>
    /// Verifies that the provided list is not empty.
    /// </summary>
    /// <typeparam name="T">Type of items in the list.</typeparam>
    /// <param name="list">The list to check.</param>
    /// <param name="details">Details on what is expected</param>
    /// <param name="paramName">The name of the parameter (optional, for exception messaging).</param>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void NotEmptyList<T>([NotNull] IList<T>? list, string details, [CallerArgumentExpression("list")] string? paramName = null)
    {
        NotNull(list, paramName);
        if (list.Count == 0)
        {
            ThrowListEmptyException(details, paramName);
        }
    }

    [DoesNotReturn]
    private static void ThrowInvalidName(string kind, string name) =>
        throw new SKException($"A {kind} can contain only ASCII letters, digits, and underscores: '{name}' is not a valid name.");

    [DoesNotReturn]
    internal static void ThrowArgumentNullException(string? paramName) =>
        throw new ArgumentNullException(paramName);

    [DoesNotReturn]
    internal static void ThrowArgumentWhiteSpaceException(string? paramName) =>
        throw new ArgumentException("The value cannot be an empty string or composed entirely of whitespace.", paramName);

    [DoesNotReturn]
    internal static void ThrowArgumentOutOfRangeException<T>(string? paramName, T actualValue, string message) =>
        throw new ArgumentOutOfRangeException(paramName, actualValue, message);

    [DoesNotReturn]
    private static void ThrowListEmptyException(string details, string? paramName) =>
        throw new ArgumentException($"The list cannot be empty. {details}", paramName);
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Runtime.CompilerServices;
using System.Text.RegularExpressions;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Diagnostics;

internal static class Verify
{
    private static readonly Regex s_asciiLettersDigitsUnderscoresRegex = new("^[0-9A-Za-z_]*$");

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void NotNull([NotNull] object? obj, [CallerArgumentExpression(nameof(obj))] string? paramName = null)
    {
        if (obj is null)
        {
            ThrowArgumentNullException(paramName);
        }
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void NotEmpty([NotNull] string? str, string? message = null, [CallerArgumentExpression(nameof(str))] string? paramName = null)
    {
        NotNull(str, paramName);
        if (string.IsNullOrWhiteSpace(str))
        {
            ThrowValidationException(ValidationException.ErrorCodes.EmptyValue, message);
        }
    }

    internal static void ValidSkillName([NotNull] string? skillName)
    {
        NotEmpty(skillName, "The skill name cannot be empty");
        if (!s_asciiLettersDigitsUnderscoresRegex.IsMatch(skillName))
        {
            ThrowInvalidName("skill name", skillName);
        }
    }

    internal static void ValidFunctionName([NotNull] string? functionName)
    {
        NotEmpty(functionName, "The function name cannot be empty");
        if (!s_asciiLettersDigitsUnderscoresRegex.IsMatch(functionName))
        {
            ThrowInvalidName("function name", functionName);
        }
    }

    internal static void ValidFunctionParamName([NotNull] string? functionParamName)
    {
        NotEmpty(functionParamName, "The function parameter name cannot be empty");
        if (!s_asciiLettersDigitsUnderscoresRegex.IsMatch(functionParamName))
        {
            ThrowInvalidName("function parameter name", functionParamName);
        }
    }

    internal static void StartsWith(string text, string prefix, string message)
    {
        NotEmpty(text);
        NotNull(prefix);
        if (!text.StartsWith(prefix, StringComparison.OrdinalIgnoreCase))
        {
            ThrowValidationException(ValidationException.ErrorCodes.MissingPrefix, message);
        }
    }

    internal static void DirectoryExists(string path)
    {
        if (!Directory.Exists(path))
        {
            ThrowValidationException(ValidationException.ErrorCodes.DirectoryNotFound, $"Directory not found: {path}");
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

                NotEmpty(p.Name, "The parameter name is empty");

                if (!seen.Add(p.Name))
                {
                    throw new KernelException(
                        KernelException.ErrorCodes.InvalidFunctionDescription,
                        $"The function has two or more parameters with the same name '{p.Name}'");
                }
            }
        }
    }

    [DoesNotReturn]
    private static void ThrowInvalidName(string kind, string name) =>
        throw new KernelException(
            KernelException.ErrorCodes.InvalidFunctionDescription,
            $"A {kind} can contain only ASCII letters, digits, and underscores: '{name}' is not a valid name.");

    [DoesNotReturn]
    internal static void ThrowArgumentNullException(string? paramName) =>
        throw new ArgumentNullException(paramName);

    [DoesNotReturn]
    internal static void ThrowArgumentOutOfRangeException<T>(string? paramName, T actualValue, string message) =>
        throw new ArgumentOutOfRangeException(paramName, actualValue, message);

    [DoesNotReturn]
    internal static void ThrowValidationException(ValidationException.ErrorCodes errorCodes, string? message) =>
        throw new ValidationException(errorCodes, message);
}

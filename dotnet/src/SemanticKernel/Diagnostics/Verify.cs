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
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void NotNull([NotNull] object? obj, string message)
    {
        if (obj != null) { return; }

        throw new ValidationException(ValidationException.ErrorCodes.NullValue, message);
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void NotEmpty([NotNull] string? str, string message)
    {
        NotNull(str, message);
        if (!string.IsNullOrWhiteSpace(str)) { return; }

        throw new ValidationException(ValidationException.ErrorCodes.EmptyValue, message);
    }

    internal static void ValidSkillName([NotNull] string? skillName)
    {
        NotEmpty(skillName, "The skill name cannot be empty");
        Regex pattern = new("^[0-9A-Za-z_]*$");
        if (!pattern.IsMatch(skillName))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidFunctionDescription,
                "A skill name can contain only latin letters, 0-9 digits, " +
                $"and underscore: '{skillName}' is not a valid name.");
        }
    }

    internal static void ValidFunctionName([NotNull] string? functionName)
    {
        NotEmpty(functionName, "The function name cannot be empty");
        Regex pattern = new("^[0-9A-Za-z_]*$");
        if (!pattern.IsMatch(functionName))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidFunctionDescription,
                "A function name can contain only latin letters, 0-9 digits, " +
                $"and underscore: '{functionName}' is not a valid name.");
        }
    }

    internal static void ValidFunctionParamName([NotNull] string? functionParamName)
    {
        NotEmpty(functionParamName, "The function parameter name cannot be empty");
        Regex pattern = new("^[0-9A-Za-z_]*$");
        if (!pattern.IsMatch(functionParamName))
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidFunctionDescription,
                "A function parameter name can contain only latin letters, 0-9 digits, " +
                $"and underscore: '{functionParamName}' is not a valid name.");
        }
    }

    internal static void StartsWith(string text, string prefix, string message)
    {
        NotEmpty(text, "The text to verify cannot be empty");
        NotNull(prefix, "The prefix to verify is empty");
        if (text.StartsWith(prefix, StringComparison.InvariantCultureIgnoreCase)) { return; }

        throw new ValidationException(ValidationException.ErrorCodes.MissingPrefix, message);
    }

    internal static void DirectoryExists(string path)
    {
        if (Directory.Exists(path)) { return; }

        throw new ValidationException(
            ValidationException.ErrorCodes.DirectoryNotFound,
            $"Directory not found: {path}");
    }

    /// <summary>
    /// Make sure every function parameter name is unique
    /// </summary>
    /// <param name="parameters">List of parameters</param>
    internal static void ParametersUniqueness(IEnumerable<ParameterView> parameters)
    {
        var x = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var p in parameters)
        {
            if (x.Contains(p.Name))
            {
                throw new KernelException(
                    KernelException.ErrorCodes.InvalidFunctionDescription,
                    $"The function has two or more parameters with the same name '{p.Name}'");
            }

            NotEmpty(p.Name, "The parameter name is empty");
            x.Add(p.Name);
        }
    }

    internal static void GreaterThan<T>(T value, T min, string message) where T : IComparable<T>
    {
        int cmp = value.CompareTo(min);

        if (cmp <= 0)
        {
            throw new ValidationException(ValidationException.ErrorCodes.OutOfRange, message);
        }
    }

    public static void LessThan<T>(T value, T max, string message) where T : IComparable<T>
    {
        int cmp = value.CompareTo(max);

        if (cmp >= 0)
        {
            throw new ValidationException(ValidationException.ErrorCodes.OutOfRange, message);
        }
    }
}

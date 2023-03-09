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

    /// <summary>
    /// Make sure value is greater than some threshold.
    /// </summary>
    /// <param name="value">The value to be compared</param>
    /// <param name="lower">The lower bound</param>
    /// <param name="valueName">The name of the value. Will use it in the error message</param>
    internal static void GreaterThan<T>(T value, T lower, string? valueName = null) where T : IComparable<T>
    {
        if (value.CompareTo(lower) > 0) { return; }

        throw new ValidationException(
            ValidationException.ErrorCodes.OutOfRange, $"{valueName ?? "Value"} of {value} is not greater than {lower})");
    }

    /// <summary>
    /// Make sure value is greater than or equal to some threshold.
    /// </summary>
    /// <param name="value">The value to be compared</param>
    /// <param name="lower">The lower bound</param>
    /// <param name="valueName">The name of the value. Will use it in the error message</param>
    internal static void GreaterThanOrEqualTo<T>(T value, T lower, string? valueName = null) where T : IComparable<T>, IEquatable<T>
    {
        if (value.CompareTo(lower) > 0 || value.Equals(lower)) { return; }

        throw new ValidationException(
            ValidationException.ErrorCodes.OutOfRange, $"{valueName ?? "Value"} of {value} is less than {lower})");
    }

    /// <summary>
    /// Make sure value is less than some threshold.
    /// </summary>
    /// <param name="value">The value to be compared</param>
    /// <param name="upper">The upper bound</param>
    /// <param name="valueName">The name of the value. Will use it in the error message</param>
    internal static void LessThan<T>(T value, T upper, string? valueName = null) where T : IComparable<T>
    {
        if (value.CompareTo(upper) < 0) { return; }

        throw new ValidationException(
            ValidationException.ErrorCodes.OutOfRange, $"{valueName ?? "Value"} of {value} is not less than {upper})");
    }

    /// <summary>
    /// Make sure value is less than or equal to some threshold.
    /// </summary>
    /// <param name="value">The value to be compared</param>
    /// <param name="upper">The upper bound</param>
    /// <param name="valueName">The name of the value. Will use it in the error message</param>
    internal static void LessThanOrEqualTo<T>(T value, T upper, string? valueName = null) where T : IComparable<T>, IEquatable<T>
    {
        if (value.CompareTo(upper) < 0 || value.Equals(upper)) { return; }

        throw new ValidationException(
            ValidationException.ErrorCodes.OutOfRange, $"{valueName ?? "Value"} of {value} is greater than {upper})");
    }

    /// <summary>
    /// Make sure value is within range (non-inclusive).
    /// </summary>
    /// <param name="value">The value to be compared</param>
    /// <param name="lower">The lower bound</param>
    /// <param name="upper">The upper bound</param>
    /// <param name="valueName">The name of the value. Will use it in the error message</param>
    internal static void WithinRange<T>(T value, T lower, T upper, string? valueName = null) where T : IComparable<T>
    {
        if (value.CompareTo(lower) > 0 && value.CompareTo(upper) < 0) { return; }

        throw new ValidationException(
            ValidationException.ErrorCodes.OutOfRange, $"{valueName ?? "Value"} of {value} is out of range ({lower}, {upper})");
    }

    /// <summary>
    /// Make sure value is within range (inclusive).
    /// </summary>
    /// <param name="value">The value to be compared</param>
    /// <param name="lower">The lower bound</param>
    /// <param name="upper">The upper bound</param>
    /// <param name="valueName">The name of the value. Will use it in the error message</param>
    internal static void WithinRangeInclusive<T>(T value, T lower, T upper, string? valueName = null) where T : IComparable<T>, IEquatable<T>
    {
        if ((value.CompareTo(lower) > 0 || value.Equals(lower)) &&
            (value.CompareTo(upper) < 0 || value.Equals(upper))) { return; }

        throw new ValidationException(
            ValidationException.ErrorCodes.OutOfRange, $"Value {value} is out of range [{lower}, {upper}]");
    }
}

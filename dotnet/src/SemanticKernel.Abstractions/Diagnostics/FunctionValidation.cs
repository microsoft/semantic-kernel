// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.RegularExpressions;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Diagnostics;

/// <summary>
/// Class with methods to validate parameters of SK functions.
/// </summary>
public static class FunctionValidation
{
    private static readonly Regex s_asciiLettersDigitsUnderscoresRegex = new("^[0-9A-Za-z_]*$");

    /// <summary>
    /// Validates skill name.
    /// </summary>
    /// <param name="skillName">Skill name. Can contain only ASCII letters, digits, and underscores.</param>
    public static void ValidSkillName([NotNull] string? skillName)
    {
        Verify.NotNullOrWhiteSpace(skillName);

        if (!s_asciiLettersDigitsUnderscoresRegex.IsMatch(skillName))
        {
            ThrowInvalidName("skill name", skillName);
        }
    }

    /// <summary>
    /// Validates function name.
    /// </summary>
    /// <param name="functionName">Function name. Can contain only ASCII letters, digits, and underscores.</param>
    public static void ValidFunctionName([NotNull] string? functionName)
    {
        Verify.NotNullOrWhiteSpace(functionName);

        if (!s_asciiLettersDigitsUnderscoresRegex.IsMatch(functionName))
        {
            ThrowInvalidName("function name", functionName);
        }
    }

    /// <summary>
    /// Validates function parameter name.
    /// </summary>
    /// <param name="functionParamName">Function parameter name. Can contain only ASCII letters, digits, and underscores.</param>
    public static void ValidFunctionParamName([NotNull] string? functionParamName)
    {
        Verify.NotNullOrWhiteSpace(functionParamName);

        if (!s_asciiLettersDigitsUnderscoresRegex.IsMatch(functionParamName))
        {
            ThrowInvalidName("function parameter name", functionParamName);
        }
    }

    /// <summary>
    /// Make sure every function parameter name is unique
    /// </summary>
    /// <param name="parameters">List of parameters</param>
    public static void ParametersUniqueness(IList<ParameterView> parameters)
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
                        throw new ArgumentNullException(paramName);
                    }
                    else
                    {
                        throw new ArgumentException("The value cannot be an empty string or composed entirely of whitespace.", paramName);
                    }
                }

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
}

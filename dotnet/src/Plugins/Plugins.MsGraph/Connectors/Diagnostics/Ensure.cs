// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;

namespace Microsoft.SemanticKernel.Skills.MsGraph.Connectors.Diagnostics;

/// <summary>
/// Internal data validation class.
/// </summary>
internal static class Ensure
{
    /// <summary>
    /// Ensures the given parameter is not null or does not contain only white-space characters.
    /// Throws an <see cref="ArgumentException"/> if the parameter is invalid.
    /// </summary>
    /// <exception cref="ArgumentException"></exception>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void NotNullOrWhitespace([NotNull] string parameter, [NotNull] string parameterName)
    {
        if (string.IsNullOrWhiteSpace(parameter))
        {
            throw new ArgumentException($"Parameter '{parameterName}' cannot be null or whitespace.", parameterName);
        }
    }

    /// <summary>
    /// Ensures the given parameter is not null.
    /// Throws an <see cref="ArgumentNullException"/> if the parameter is invalid.
    /// </summary>
    /// <exception cref="ArgumentNullException"></exception>
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void NotNull([NotNull] object parameter, [NotNull] string parameterName)
    {
        if (parameter == null)
        {
            throw new ArgumentNullException($"Parameter '{parameterName}' cannot be null.", parameterName);
        }
    }
}

// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;

namespace Microsoft.SemanticKernel.Skills.MsGraph.Diagnostics;

internal static class Ensure
{
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void NotNullOrWhitespace([NotNull] string parameter, [NotNull] string parameterName)
    {
        if (string.IsNullOrWhiteSpace(parameter))
        {
            throw new ArgumentException($"Parameter '{parameterName}' cannot be null or whitespace.", parameterName);
        }
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void NotNull([NotNull] object parameter, [NotNull] string parameterName)
    {
        if (parameter == null)
        {
            throw new ArgumentNullException($"Parameter '{parameterName}' cannot be null.", parameterName);
        }
    }
}

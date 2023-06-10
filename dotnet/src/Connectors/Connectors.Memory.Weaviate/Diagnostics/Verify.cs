// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Diagnostics;

internal static class Verify
{
    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void NotNull([NotNull] object? obj, string message)
    {
        if (obj != null) { return; }

        throw new ArgumentNullException(null, message);
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void NotNullOrEmpty([NotNull] string? str, string message)
    {
        NotNull(str, message);
        if (!string.IsNullOrWhiteSpace(str)) { return; }

        throw new ArgumentOutOfRangeException(message);
    }

    [MethodImpl(MethodImplOptions.AggressiveInlining)]
    internal static void ArgNotNullOrEmpty([NotNull] string? str, string paramName, [CallerMemberName] string? caller = default)
    {
        NotNull(str, paramName);
        if (!string.IsNullOrWhiteSpace(str)) { return; }

        throw new ArgumentException(paramName, $"Parameter {paramName} cannot be empty." + (!string.IsNullOrEmpty(caller) ? $"({caller})" : string.Empty));
    }
}

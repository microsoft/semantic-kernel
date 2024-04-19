// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for <see cref="IEnumerable{T}"/> interface.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class EnumerableExtensions
{
    public static bool IsNotEmpty<T>(this IEnumerable<T> enumerable) =>
        enumerable is not ICollection<T> collection || collection.Count != 0;
}

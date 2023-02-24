// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Text;

internal static class StringExtensions
{
    [SuppressMessage("Globalization", "CA1309:Use ordinal StringComparison", Justification = "By design")]
    internal static bool EqualsIgnoreCase(this string src, string value)
    {
        return src.Equals(value, StringComparison.InvariantCultureIgnoreCase);
    }
}

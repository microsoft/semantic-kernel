// Copyright (c) Microsoft. All rights reserved.
namespace SemanticKernel.Data.Nl2Sql.Library.Internal;

using System;

internal static class StringExtensions
{
    public static bool TryGetValue(this string source, out string value, string label, bool require = true)
    {
        value = string.Empty;

        if (!string.IsNullOrWhiteSpace(label))
        {
            int index = source.IndexOf($"{label}:", StringComparison.OrdinalIgnoreCase);
            if (index == -1)
            {
                if (require)
                {
                    return false;
                }

                value = source;
            }
            else
            {
                value = source.Substring(index + label.Length + 1);
            }
        }
        else
        {
            value = source;
        }

        return true;
    }
}

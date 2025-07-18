// Copyright (c) Microsoft. All rights reserved.

using System.Text.RegularExpressions;

namespace Microsoft.SemanticKernel.Process.Workflows.Extensions;

internal static class StringExtensions
{
    private static readonly Regex s_regex = new(@"^```(?:\w*)\s*([\s\S]*?)\s*```$", RegexOptions.Compiled | RegexOptions.Multiline);

    public static string TrimJsonDelimeter(this string value)
    {
        Match match = s_regex.Match(value.Trim());
        if (match.Success)
        {
            return match.Groups[1].Value.Trim();
        }

        return value.Trim();
    }
}

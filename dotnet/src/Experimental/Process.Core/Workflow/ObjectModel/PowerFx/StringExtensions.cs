// Copyright (c) Microsoft. All rights reserved.

using System.Text.RegularExpressions;

namespace Microsoft.SemanticKernel.Process.Workflows.PowerFx;

internal static class StringExtensions
{
    private static readonly Regex s_regex = new(@"^```json\s*([\s\S]*?)\s*```$", RegexOptions.Compiled | RegexOptions.Multiline);

    public static string TrimJsonDelimeter(this string value)
    {
        Match match = s_regex.Match(value);
        if (match.Success)
        {
            return match.Groups[0].Value.Trim();
        }

        return value;
    }
}

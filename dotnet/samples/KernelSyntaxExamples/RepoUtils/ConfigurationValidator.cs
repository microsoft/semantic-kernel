#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using System;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.RegularExpressions;
using Xunit.Abstractions;

namespace RepoUtils;

public static class ConfigurationValidator
{
    public static bool Validate(string exampleName,
        string?[] args,
        ITestOutputHelper output,
        string? exampleNameSuffix = null,
        [CallerArgumentExpression("args")] string argsExpression = "")
    {
        var paramsNames = Regex.Matches(argsExpression!, @$"(?<={nameof(TestConfiguration)}\.)[A-Za-z0-9-_.]+");
        if (paramsNames.Count == 0 || string.IsNullOrWhiteSpace(exampleName) || args.Length != paramsNames.Count)
        {
            throw new ArgumentException("Invalid arguments to validate configuration.");
        }

        var dict = Enumerable.Range(0, args.Length).ToDictionary(i => paramsNames[i].Value, i => args[i]);
        string invalidParams = string.Join(", ", dict.Where(m => string.IsNullOrEmpty(m.Value)).Select(m => m.Key));
        if (invalidParams.Length > 0)
        {
            if (!string.IsNullOrWhiteSpace(exampleNameSuffix))
            {
                exampleName += $" ({exampleNameSuffix})";
            }

            output.WriteLine($"{exampleName} requires the following parameters to be set in TestConfiguration: {invalidParams}\nSkipping example.");
            return false;
        }

        return true;
    }
}

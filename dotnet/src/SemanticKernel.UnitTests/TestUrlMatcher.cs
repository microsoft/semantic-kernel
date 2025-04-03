// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using Xunit;

namespace SemanticKernel.UnitTests;

public class TestUrlMatcher
{
    private readonly static List<string> s_uriTemplates = new List<string>
    {
        "doc://{type}/{filename}",
        "log://{filename}"
    };

    [Fact]
    public void TestMather()
    {
        // Arrange
        string uri = "doc://text/hello.txt";

        // Act
        foreach (string template in s_uriTemplates)
        {
            string pattern = "^" + Regex.Escape(template)
                .Replace("\\{", "(?<")
                .Replace("}", @">[^/]+)") + "$";

            Regex regex = new Regex(pattern);

            Match match = regex.Match(uri);

            if (match.Success)
            {
                var groups = match.Groups.Cast<Group>()
                    .Where(g => g.Success && g.Name != "0")
                    .ToDictionary(g => g.Name, g => g.Value);

                foreach (var parameter in groups)
                {
                    Console.WriteLine($"{parameter.Key}: {parameter.Value}");
                }
            }
        }
    }
}
